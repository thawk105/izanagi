## 総括

`SATISFIED` 経路や P3 の bench launch 分岐は緩まない。しかし、`_MACHINE_EVALUATORS` への C06 追加で過去契約の理由コードが変わる回帰があり、machine-checkable 宣言と実装検査の強さにも乖離が残るため、このままの昇格は NO です。

### blocker

1. **[real] 過去の C06 staged 契約の理由コードが変わる**

根拠は、現在の `_evaluate_undefined` が `number in _MACHINE_EVALUATORS` を C06 専用分岐より先に評価することです。[s8c_preregistration_evidence.py:3079]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3079 )、[s8c_preregistration_evidence.py:3092]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3092 )

変更後に C06 を map へ追加すると、過去 commit の `machine_checkable: false` も一般分岐へ入り、理由が `budget-consumer-contract-undefined` から `completion-proof-not-machine-checkable` へ変わります。status は同じ `EVIDENCE_UNDEFINED` ですが、D529 が版管理対象と明記する拒否理由の意味が変わります。[D529:21866]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/docs/decisions.md:21866 )

再現手順: 昇格後の module で、基準 commit の C06 が false の commit を `PredicateRegistry.evaluate_all` に渡し、C06 の reason を確認する。昇格前との差分として上記の理由変更が現れます。

対処は、`number == 6` の false 契約分岐を map membership より先に置くことです。

### major

2. **[real] machine-checkable 宣言が実際の意味検査より強い**

stage2 plan は C06 の flag と proof 側を変更しない前提です。[stage2-plan-output.md:12]( /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1421-c06-machine-checkable-promotion/stage2-plan-output.md:12 )

一方、C06 evaluator は関数名の存在、reachable call の集合、`sha256` attribute の存在しか見ません。[s8c_preregistration_evidence.py:3491]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3491 )、[s8c_preregistration_evidence.py:3513]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3513 )

そのため、予約を launch 後へ移す、freeze の SHA を `reserve_all_cells` へ渡さない、lock や limit check を no-op 化する変異でも、名前を残せば検査を通過し得ます。`s8c_budget.py` の実処理は lock と limit state を実行時に検査していますが、evaluator はその実行関係を検査していません。[s8c_budget.py:517]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_budget.py:517 )

これは受理ゲートの直接的な緩みではありませんが、「consumer proof を機械検査できる」という外部シグナルを過大にします。最低限、flag の意味を構造検査限定と明記するか、今回の昇格を後続 wave 完了まで保留すべきです。

3. **[refuted] `SATISFIED` へ到達して受理される経路がある**

この点について stage2 plan の結論は正しいです。`_evaluate_c06` は `UNSATISFIED` または `EVIDENCE_UNDEFINED` しか返しません。[s8c_preregistration_evidence.py:3477]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3477 )、[s8c_preregistration_evidence.py:3530]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3530 )

さらに `is_satisfied` は exact な `SATISFIED` のみを認識し、allowlist は空です。[s8c_preregistration_evidence.py:288]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:288 )、[s8c_preregistration_evidence.py:3070]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3070 )。仮に evaluator を差し替えて `SATISFIED` を返しても、`ERROR/evaluator-internal-error` に倒れます。[s8c_preregistration_evidence.py:3181]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3181 )

### minor

4. **[refuted] P3 の launch 可否は C06 predicate 結果を読んでいない**

P3 は budget API を直接 import し、C06 の有効化を `registered-effective` と `do_build` で分岐しています。[p3_autonomous_workload_trial.py:103]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/p3_autonomous_workload_trial.py:103 )、[p3_autonomous_workload_trial.py:4125]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/p3_autonomous_workload_trial.py:4125 )

`evaluate_all`、`machine_checkable`、production/staged registry の参照は、射影対象の P3 と budget module にはありません。予約は launch 前、精算は terminal cell 後です。[p3_autonomous_workload_trial.py:4221]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/p3_autonomous_workload_trial.py:4221 )、[p3_autonomous_workload_trial.py:3115]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/p3_autonomous_workload_trial.py:3115 )

5. **[refuted] 負の対照の検出力は registry 移行だけでは落ちない**

負の対照が一行を削除すると、`_c06_expected_rows(tree) != _C06_EXPECTED_CELL_ROWS` で検出されます。[s8c_preregistration_evidence.py:3423]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3423 )

同じ `_evaluate_c06` が production map から呼ばれるだけなので、`UNSATISFIED` への遷移は維持されます。plan も staged 参照を production registry へ移すとしています。[stage2-plan-output.md:63]( /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1421-c06-machine-checkable-promotion/stage2-plan-output.md:63 )

6. **[refuted] C06 は現物上、唯一の staged 条件である**

現在の production map は C01、C02、C04、C05、C07、C09、C10、C11、C12 の9件で、C03/C08 はありません。[s8c_preregistration_evidence.py:3056]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3056 )

staged map は C06 のみです。[s8c_preregistration_evidence.py:3537]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3537 )

このまま昇格してよいか: **NO**。受理ゲートは緩まないものの、過去契約の理由コード回帰と、proof 宣言に対する検査不足を解消せずに production registry へ移すためです。

read-only のため pytest は実行していません。