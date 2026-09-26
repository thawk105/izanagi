## 対応表

| 対象 | 判定 | 根拠 |
|---|---|---|
| J1・前回 must-fix | **closed（親の refuted 裁定は妥当）** | 候補は [policy gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_policy.py:169) で構文検査と単独 TU compile を通る。文法は文字列・pointer 形式を拒否し、呼出先を制限する（[grammar](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/silo_policy_grammar.py:94)、[grammar の呼出規則](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/silo_policy_grammar.py:501)）。trace の R/W key は固定計装が read/write set から取り、小文字 hex に変換する（[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/external/ccbench/cc/silo/transaction.cc:606)、[trace.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/external/ccbench/include/trace.hh:65)）。不正 key は `malformed_keys` に計上され、digest に残る（[parse.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/verifier/parse.py:282)、[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_policy.py:253)）。 |
| J2・前回 must-fix | **closed** | digest は返された witness 数を `witness_count`、全 cycle 数を `total_cycles` として別々に保持し、表示は最大 8 件（[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_policy.py:244)）。39,124 cycle の例を使う test も改訂された（[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/tests/test_p3_s4_loop_policy.py:269)）。 |
| H1 | **closed** | 性能 file 登録簿に driver と用途の注記を追加した（[test_official_perf_closure.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/tests/test_official_perf_closure.py:61)）。 |

## 新しい所見 (重大度・根拠・影響 1 行・代案)

新しい must-fix はなし。方策は待機・abort により記録される取引の集合には影響しうるが（[skeleton patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/patches/silo-function-policy-variant.patch:95)）、trace key の任意文字列を作る経路は確認できない。外部要因で壊れた trace の不正 key が anomaly 辺に残る可能性はあるものの、J1 の候補由来の注入経路を示すものではない。

## 総括

**GO。残る must-fix は 0 件。** fix-3・fix-4 の差分は登録簿、件数 field、対応 test のみ。gate 順、auditor 上限、firewall、既存軸、F1〜F9、G1〜G3 に回帰は見つからなかった（静的確認）。build・pytest は依頼どおり実施していない。