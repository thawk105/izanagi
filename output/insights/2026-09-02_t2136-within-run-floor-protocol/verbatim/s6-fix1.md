## 各修正項目の対応

1. [layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/campaign/layer3_report.py:372) で固定深さの repo root 推測を廃止。pin の calibration suffix を実際の `calibration_dir` に結合し、env、`..`、絶対 path、directory 外、通常 file、SHA-256 を検査します。
2. pin file 不在は候補なしとし、`contract_pin.status = pin-file-missing` を search details に記録します。改竄や境界違反は引き続き fail-closed です。
3. authority と WAL の env 不一致は `authority-env-tag-mismatch` として記録し、pin 候補なしで report を生成します。
4. 一致した floor へ常に `protocol_match_basis` を出力。[layer3_schema.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/campaign/layer3_schema.json:257) は optional のまま3値 enumへ拡張し、schema version は v3 据え置きです。
5. M2 receipt を silo・mocc 両方の全軸を持つ形へ変更し、独立した mocc literal を期待値にしました。
6. test helper を任意の `output_root` に対応させ、入れ子 exploration root の pin 存在・不在試験を追加しました。

## 追加・変更したテスト

主な回帰は [test_layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/tests/test_layer3_report.py:3077) と [test_calibrator_certify.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/tests/test_calibrator_certify.py:431) に追加しました。

- authority/WAL env 不一致の候補なし＋記録
- SHA 不一致、他 env、絶対 path、`..`、directory、symlink escape の拒否
- 入れ子 root での pin suffix 解決
- 入れ子 root で pin 不在時に直下 floor を維持
- 最終 report 内の `receipt-derived-build-argv`
- 最終 report 内の `canonical-floor-genome`
- M2 の単一理由性

既存の legacy basis 期待値、skip、xfail、テスト削除は変更していません。

## 実走した nodeid と結果

実際に開始できた pytest nodeid は0件です。したがってテスト成功の申告はありません。

代替の静的・実体診断では以下を確認しました。

- 変更した全 Python fileの AST parse
- `layer3_schema.json` の JSON parseとDraft 7 schema検査
- 入れ子 rootでの実在Pegasus pin解決
- pin不在時の直下候補維持と機械可読な記録
- SHA不一致の fail-closed
- schemaの optional fieldおよび3 literal
- M2 receiptからの独立 literal導出
- `git diff --check HEAD`

## 未実走のもの

規定の `tools/run_tests.py` で以下を試しましたが、すべて `child_started=false`、`qstat -Q preflight rc=1`、最終 rc=16 でした。

- 新設・変更した layer3 pin／入れ子 root／basis nodeid
- M2 nodeidとschema v2 nodeid
- `test_m2_normal_formal_campaign_remains_accepted`
- `test_trial_registry.py`
- `test_autonomous_trial_completeness.py`
- 内容走査 `test_v2_modules_have_no_env_literals_outside_registry`
- AST走査 `test_calibration_capability_issuer_has_one_certify_call_site`
- AST走査 `test_reviewed_ccbench_measurement_launches_use_bounded_sites`

よって状態は「実装済み・pytest未実走」です。

## 波及可能性の静的列挙

- production caller: `build_report`、`render`、`build_accepted_report`
- 所有外 caller: `autonomous_trial_completeness.py`、`p3_autonomous_workload_trial.py`、`s1_report.py`
- shared fixture: `test_layer3_report.py::_campaign` と `_copy_contract_calibration`
- consumer tests: `test_t126_qualification_artifacts.py`、`test_trial_registry.py`、`test_autonomous_trial_completeness.py`、`test_s1_report.py`、`test_s8b_oracle_driver.py`
- 内容・AST走査: `test_env_contract.py`、`test_ccbench_spawn_sites.py`

## 総括

6項目は実装済みです。変更は指定された7 fileだけで、commit・add・stashは行っていません。禁止対象とdocsに差分はなく、凍結済みPegasus artifactのSHA-256も `753f535a...`、`94a4b79f...` のままです。

pytestはdispatch基盤のrc=16により未実走のため、完了済みとは申告しません。