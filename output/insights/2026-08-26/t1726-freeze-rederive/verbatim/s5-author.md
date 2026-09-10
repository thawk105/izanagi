実装は完了しました。テストは実行基盤の都合で未実走です。

## 変更前の挙動

v2/v3 verifier は receipt・report・run-start の自己整合だけを確認し、ratified legacy freeze から導いた条件とは照合していませんでした。`launch_admission.binding.measurement_head` も receipt と比較していませんでした。

## 実装範囲

[s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:696) に以下を追加しました。

- `load_legacy_freeze()` を引数なしで呼び、verifier checkout を権威 root に使用
- legacy holdout 名、6-key 集合、4-key canonical 投影、`DERANGEMENT` の exact 検査
- `resolve_arm_input` による content digest 再導出
- binding の `measurement_head` 比較
- 追加 import はすべて関数ローカル
- expected `arm_binding_digest` 比較は追加せず、既存 gate から従う旨をコメント化
- v2/v3 のみに `[receipt-freeze-arm-binding]` を適用

この gate は freeze から再導出できない v2/v3 arm record を拒否します。v1 や、検証対象 repository に legacy freeze の複製がないことは拒否しません。

[test_s8c_acceptance_receipt_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:78) は、temp repo に off artifact を生成して commit し、その実 OID と resolver の結果を六セルで使う fixture に変更しました。legacy freeze は複製していません。

追加テストは次のとおりです。

- M1: 自己整合した整数 `80 → 79` descriptor の拒否
- M2: legacy entry の key 集合 drift
- M3: resolver が消費しない追加 key による `DERANGEMENT` drift
- M4: binding `measurement_head` 不一致
- 正例: 既存 `test_v2_producer_equivalent_full_verify_drops_only_c02`
- 既存 v3 正例も実 resolver fixture を共有

## 検証状況

以下の file 全体を既定 runner で実走しようとしましたが、test 子は起動していません。

`orchestrator/tests/test_s8c_acceptance_receipt_v2.py`

通常走と collect-only の双方が Pegasus dispatch の `qstat -Q preflight rc=1`、runner rc=16 で終了しました。login-node 側も 16 GiB user cgroup 上限近傍で、最低 1 GiB の local 枠を確保できませんでした。

したがって、実走済み nodeid はありません。次も未実走です。

- 制約 meta-test: `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
- 所有外正例: `test_trial_registry.py::test_p5_six_complete_terminal_reports_pass_acceptance`

静的には Python AST parse、`git diff --check`、変更ファイル制約を通過しています。dispatch が生成した一時 `output/pegasus-dispatch` ファイルは除去済みです。

## 波及可能性

- `trial_registry.py` は v3 receipt producer のため意味的影響を受けますが、権威 root を verifier checkout に固定したため temp repo 正例を `legacy-read` で拒否しない設計です。
- `layer3_report.py` は再検証済み capability の consumer です。現在は全 receipt が非 certifying のため、現成果物の値は変わりません。
- `s8b_ratified_freeze`、`s8b_holdout_freeze`、`s8c_arm_inputs` を共有 authority として遅延利用します。
- `test_s8c_acceptance_receipt.py` の v1、`test_trial_registry.py`、`test_layer3_report.py`、`test_reflux_originless_compatibility.py` は回帰候補です。schema と serialized bytes は変更していません。

## 総括

- 変更ファイル: 指定された 2 本のみ
- 追加 gate: `[receipt-freeze-arm-binding]`
- 追加 test: M1〜M4 の 4 本、既存 v2/v3 正例を実 resolver 化
- 実走状況: 実装済み・未実走。runner rc=16 で test 未起動
- 残った赤: 実測された test failure はありませんが、対象 file、meta-test、所有外正例は未検証
- `git add`、`git commit` は実施していません