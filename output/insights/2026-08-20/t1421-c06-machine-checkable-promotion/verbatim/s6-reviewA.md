## 総括

### blocker

- [refuted] 契約 JSON の差分は C06 の `machine_checkable: true` のみです。[contract:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:264)。
- [refuted] evaluator の判定ロジックは HEAD と AST 比較で全 C01-C12 一致。registry は `_evaluate_c06` 後に移動され、C06 は数値順、staged registry は空です。[evidence:3464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3464) [evidence:3524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3524)
- [refuted] `DECIDER_VERSION` は正確に v6 です。[preregistration:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration.py:51)

### major

- [refuted] g10 record は `prepare_revision` の生成結果と完全一致しました。generation=10、D529、12件の section6 hash、evidence hash、protected hash、g9 raw hash による supersedes hash を再計算で確認しました。[preregistration:2035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration.py:2035) [g10:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g10.json:1)
- [refuted] staged negative-control wrapper は撤去され、C06 mutation は main dispatcher に統合されています。旧 wrapper の有効経路と新 branch の AST は一致し、変異後から H2/swapped 行が1件だけ除去されます。[predicates:1135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_predicates.py:1135)

### minor

- [refuted] core test の4 hash は再計算値と一致します。current=`dafd8d...701a`、NUL=`be5c...e410`、CR=`42a3...0ee`、LF=`063e...126`。[core:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_core.py:806) [core:1196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_core.py:1196)
- [refuted] C06 の invariant は checks 4件、exclusions 5件で、契約 token と実コード関数名に一致し、missing=0 でした。[invariant:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_invariant.py:80) [invariant:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_invariant.py:122)
- [refuted] C03/C08 の evaluator、契約、negative-control、registry への変更はありません。staged 関連の active な古い文言もなく、残る `_STAGED_EVALUATORS` は要求どおりの空 sentinel とその検査だけです。[predicates:1086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_predicates.py:1086) [predicates:3655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_predicates.py:3655)

pytest は read-only 条件に従い未実行です。静的検査と `git diff --check` は問題ありません。

このまま統合commitしてよいか: YES  
根拠: D529 とプラン v2 の変更面に正確に一致し、判定ロジックの緩和や C03/C08 の混入も確認されなかったため。