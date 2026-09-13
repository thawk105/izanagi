## 総括

単位 1 を実装しました。**実装済み・未実走**です。変更は許可された 2 ファイルのみ。docs・共有 fixture・consumer は未変更、commit・push・branch 操作もしていません。

## 現行の受理・拒否挙動

変更前：

- `p3_autonomous_workload_trial.py:1882–1883` は、bytes と root を `producer.result_record_bytes`／`producer.evidence_root` から取得。
- `test_p3_autonomous_workload_trial.py:10367–10371` は、共有 fixture の `item["evidence_path"]` を member 入力へ設定。

変更後は、producer 経路が runtime root 内の導出された 33 ファイルを要求します。欠落・順序不正・path 重複・record と path の不一致・安全に読めないファイルは、既存の `AutonomousTrialError` へ返し、formal 評価へ進めません。

`evaluate_formal_origin` の直接呼出し経路と originless 経路の受理条件は変更していません。

## 変更した file と意図

- `orchestrator/campaign/p3_autonomous_workload_trial.py`：3 field を削除し、path 導出、runtime root 固定、安全な disk 回収と検証を実装。
- `orchestrator/tests/test_p3_autonomous_workload_trial.py`：正例の材料を導出先へ配置し、回収機構の負例を追加。

公開 path 関数は完全な record の検証を要求するため、envelope 構築時には利用できません（`reflux_result_evidence.py:959`）。規則の重複は `_origin_result_evidence_path` 1 箇所に限定し、既存 `_safe_path_token` を再利用。回収後の照合には公開関数を使用しています。

## 新設した負例と単一理由性

以下は**静的確認のみで、実走確認は未完了**です。

| 指定ケース | 検査方法 |
|---|---|
| 別 path の申告 | 削除 field の指定が TypeError となり、実 envelope が導出値を使うことを検査 |
| record が 32 件 | 正常配置・seal 後に 1 ファイルだけ削除 |
| ordinal の順序入替え | 通常の envelope 構築でも拒否されることを確認後、構築後破損として回収検査を狙う |
| 別 q の record | q0 の場所だけ q1 の正常 bytes に置換 |
| 別 root の申告 | 削除 field の指定拒否と、実 consumer に渡る runtime root を検査 |

負例では consumer 未到達、terminal 未設定、ledger 不変も検査します。追加で member 数不足、path 重複、symlink、unsafe token を扱いました。

## 実走した nodeid と結果

**実走した nodeid はありません。**

- `tools/run_tests.py`：qstat preflight 失敗、rc=16、child 未起動。
- 直接 pytest：PreToolUse hook がログインノード上の pytest として拒否。

実行対象には変更先、originless compatibility、formal consumer、および探索で見つけた `test_plain_runner_coverage.py`／`test_pytest_collection_config.py` を含めました。

新設 nodeid：

- `test_origin_runtime_collects_only_producer_owned_evidence`（9 ケース）
- `test_origin_evidence_path_reuses_result_evidence_token_rejection`（14 ケース）

構文解析・`git diff --check` は成功。既存 test 関数はすべて AST 単位で変更なしと確認しました。

## 所有外への波及

- repo 内の両 dataclass の直接構築箇所は、変更したテスト helper に限定されていました。
- `test_reflux_originless_compatibility.py:134` は `_origin_public_inputs` を共有するため、材料配置変更の間接影響があります。再実走が必要です。
- 共有 fixture builder／baseline は変更していません。
- `test_reflux_formal_consumer.py:350,703` の直接 consumer 呼出しは、従来の bytes 引数を維持できます。
- repo 外で削除 field を指定する caller は TypeError になります。
- 既存の非公開読取り helper／token helper に依存します。

## 実装できなかった項目

実装項目の欠落はありません。テスト実走と、実走による単一理由性・公開正例継続通過の確認が未完了です。原因は dispatch 基盤の失敗と直接 pytest の hook 拒否です。