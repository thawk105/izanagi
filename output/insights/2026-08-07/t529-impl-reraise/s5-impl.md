## 実装内容

- [calibration_verify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:1)
  - `env_contract` に依存しない較正検証 leaf を新設。
  - path 封じ込め、1 回だけの bytes read、SHA、v2 schema、env/clock/policy、grandfathered v1 を検証。
  - `AttestationError` と `VerifiedCalibration` を定義。

- [env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:1029)
  - 公開型・定数を leaf から再公開。
  - `load_verified_calibration` を契約型検査、素値抽出、leaf 委譲だけの wrapper に変更。

- [silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:254)
  - `_runtime_module_paths` に leaf を1行追加。

- [test_env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_attestation.py:1058)
  - leaf 直接負例、wrapper 委譲固定、import 閉包、登録済み較正2件の正例を追加。

- [test_env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:82)
  - `V2_ENV_NEUTRAL_MODULES` へ `(calibration_verify.py, None)` を追加し、所属固定テストを追加。

- [test_silo_ladder_rung1_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_silo_ladder_rung1_driver.py:927)
  - runtime module exact-set の期待値へ leaf を追加。

文書・`output/` は編集せず、`git add`・commit も行っていません。既存の未追跡 `output/insights/2026-08-07_t529-impl-reraise/` にも触れていません。

## 検証結果

pytest は次の範囲を `tools/run_tests.py` 経由で2回試行しました。

- `orchestrator/tests/test_env_attestation.py` 全体
- `test_env_contract.py::test_v2_modules_have_no_env_literals_outside_registry`
- `test_env_contract.py::test_calibration_verify_is_in_v2_env_neutral_module_closure`
- `test_silo_ladder_rung1_driver.py::test_runtime_binding_covers_all_execution_semantics_modules`

いずれもテスト開始前に `qstat -Q preflight rc=1`、runner `rc=16` で停止しました。sandbox 外の `/run/user/...` にローカル予約台帳を作れないため dispatch へ倒れ、dispatch infrastructure も利用不能でした。したがって、これらは「実装済み・pytest 未実走」であり、緑・closed とは申告しません。

実施済みの非 pytest 検査は以下です。

- `py_compile`: 変更した Python 6ファイルに成功
- `git diff --check`: 成功
- 753f/94a4 の両較正を leaf で読む動的 smoke: ACCEPT
- wrapper の `AttestationError` / `VerifiedCalibration` alias 同一性: 確認済み
- fresh import で leaf が `campaign.env_contract` をロードしないこと: 確認済み
- runtime/AST 閉包の静的確認: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし

新設・改名したテスト名を制約する専用 meta-test は検索上ありませんでした。

## caller・consumer への波及

本番の全直接 caller は次の7箇所です。

- [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/loop.py:86)
- [t126_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/qualification/t126_driver.py:441)
- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2762)
- [s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_driver.py:789)
- [s8b_oracle_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_report.py:1230)
- [s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:1820)
- [silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:1940)

直接呼び出す consumer test は `test_env_attestation.py`、`test_env_contract.py`、`test_calibrator_certify.py`、`test_s8b_floor_campaign.py`、`test_s8b_oracle_driver.py`、`test_s8b_ratified_verify.py`、`test_silo_ladder_rung1_driver.py` です。mock/spy consumer として `test_t126_qualification_driver.py`、`test_campaign.py`、`test_s8b_oracle_report.py` も影響候補です。

型 consumer は `execution_guard.py` と `s8b_oracle_driver.py`、例外 consumer は `calibrator/cli.py` および上記 campaign 各入口です。公開 alias を維持したため、既存の `isinstance(..., env_attestation.VerifiedCalibration)` と `except env_attestation.AttestationError` はそのまま成立します。

共有 fixture は既存 `_required_artifact` と `test_schema_v2._valid_document` を再利用しました。登録済み較正 artifact は読み取り専用です。意図された成果物上の波及は、runtime module 閉包追加による将来の `runtime_modules_sha256` 変更だけです。

## 受理・拒否集合の同一性

処理順序は旧実装と同一です。

1. wrapper で `ExecutionEnvironmentContract` 型を検査。
2. leaf で `repo_root` 型・strict resolve・repository-relative path・封じ込め・存在を検査。
3. artifact を一度だけ読み、その同じ bytes で SHA と schema を検証。
4. `required` では env、clock、effective-clock tolerance/policy を同じ比較で判定。
5. `none` では同じ grandfathered SHA の bytes だけを受理し、duplicate key と top-level 型を同じ規則で検査。
6. 未知 mode は同じ `AttestationError` メッセージで拒否。

schema validator、policy 定数、grandfathered SHA、例外文言の意味は変更していません。wrapper の委譲 test により旧検証経路へ戻る変異を、leaf 直接負例により SHA・escape・env・clock・policy・duplicate-key の恒真化を検出する構成です。

## 総括

較正検証を `env_contract` 非依存の共有 leaf へ抽出し、wrapper、2閉包、要求された正負テストを実装しました。静的検査と動的 smoke は成功していますが、Pegasus dispatch infrastructure のため pytest は未実走です。