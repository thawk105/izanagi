実装済み・未実走です。コード・テスト以外は変更せず、commit も作成していません。

### 現行挙動と受理集合

変更前の public 述語は、exact key、現在 policy と等しい数値 tolerance、包含境界の全 sample 帯内を要求します。private math は非 policy tolerance、numeric string、bool、observed 長不一致を従来どおり許容します。CLI は既に benchmark 後の late gate で自己不整合 artifact を非 publish にしていました。

変更後も通常の policy 固定時の最終 publish 集合は不変です。意図的な縮小は、attempt 開始時と publish 時の policy が異なる再束縛経路だけです。early self-failure は benchmark 前に `rejection.json` のみを残します。

### 実装

- [execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:183)
  - evaluator を抽出し、`input_valid / policy_matches / band_pass` を分離。
  - public は三者の連言、private math は `band_pass` のみ。
  - median・上下限・全違反位置を返す診断 projection を追加。
  - tolerance 0/2/100、等号・1 ulp 外、空列、NaN、string、bool、非 float、長さ違いを固定。
  - `out_of_band_count == 0` でも policy 不一致なら拒否する矛盾 oracle を追加。

- [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:445)
  - `_acquisition_reasons` に canonical self-comparison を追加。
  - late gate は [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:683) に保持。
  - early rejection に構造化診断と `not_evaluated` を追加。
  - publish temp 作成後・rename 直前に、attempt/profile/publish policy の一致を検査。
  - bytes-only 独立検査、改竄 fixture、`[2101.0] * 48` の正例を [test_calibrator_certify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:268) に追加。

### 検査

成功した静的検査:

- `python3 -m py_compile`：変更した4ファイル
- `git diff --check`

pytest は次の新設 node、既存 golden、`test_plain_runner_coverage.py` meta-testを指定して2回 dispatch しましたが、いずれも `qstat -Q preflight rc=1`、runner `rc=16` でテスト開始前に停止しました。したがって緑は一件も主張しません。

既存期待値を変更していないため、静的に期待される赤は以下です。

- `test_cli_effective_clock_self_failure_is_quality_rejected_before_publish` の3 parameter
- `test_effective_clock_policy_metamorphic_wiring_producer_loader_issuer_consumer_self` の policy=2.0 側

いずれも旧 late 成果物を期待しますが、裁定された early rejection では probe 2回・`rejection.json` のみになります。これ以外の赤は回帰です。

### caller・波及

public 述語の production caller は `_independent_comparison_passes`、CLI self-comparison、`silo_ladder_rung1.py` の live attestation と receipt 再導出の2箇所です。test consumer は `test_execution_guard.py`、`test_calibrator_certify.py`、`test_env_attestation.py`、`test_env_contract.py`、`test_silo_ladder_rung1_evidence.py`、`test_silo_ladder_rung1_driver.py` です。

共有 fixture `_profile`、`_pegasus_shaped_probe`、`_invoke` を利用しています。early rejection の file-set 変更は所有外の attempt collector/final receipt manifest に波及し得ます。schema、loader、registry、`env_contract`、Pegasus tools、docs、output は未変更です。

## 総括

- evaluator・診断、early/late gate、publish policy gateを実装した。
- canonical predicate だけを受理 authority とし、診断 count は使用していない。
- published bytes の独立再読検査と改竄負例、2101 MHz 正例を追加した。
- `py_compile` と `git diff --check` は成功した。
- pytest/meta-test は dispatch infrastructure failure のため未実走。
- 既存 late 成果物期待との衝突は未変更・未解決のまま報告した。
- 最大 risk は対象・consumer test が一件も実走できていないこと。