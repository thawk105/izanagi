## 総括

D529 の C06 昇格を未コミットで完了しました。docs は編集せず、commit も作成していません。

1. 契約反転  
   [s8c_preregistration_evidence_contract.v1.json:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:264) の C06 を `true` に変更。C03/C08 は未変更。

2. registry 登録  
   [_MACHINE_EVALUATORS:3524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration_evidence.py:3524) を `_evaluate_c06:3464` 後へ移動し、C06 を追加。`_STAGED_EVALUATORS` は空集合化。判定ロジック本体は未変更。staged コメントと docstring を更新。

3. decider version  
   [s8c_preregistration.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/campaign/s8c_preregistration.py:51) を v6 に変更。

4. condition-freeze record  
   `prepare-revision` は成功しました。  
   [condition-freeze.v1.g10.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g10.json:1)

   - generation: `10`
   - decider: `s8c-decider/v6`
   - evidence hash: `dafd8d61807360c333288a00730e7c9ae13a086b61c770e7faf47fb5dd1f701a`
   - protected hash: `46811db02eff5d452aee0026f2d7eb04b8d28c7142291ad14646a950db5595b0`
   - supersedes hash: `ef24bdd64fd9fb50ac3652f3c766a2aa99e81f3b18bebd546dd33029f5ac90dd`
   - ruling: `D529`

5. negative-control とテスト更新  
   [predicates test:1135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_predicates.py:1135) へ C06 mutation を統合し、staged wrapper を撤去。C06 の registry、reason、件数を更新。  
   [core test:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_core.py:806) 以降の4 hash と v6 固定値を更新。  
   [invariant test:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1421-c06-machine-checkable-promotion/orchestrator/tests/test_s8c_preregistration_invariant.py:80) 以降へ C06 の4 checks、5 exclusions を追加。

テスト結果:

- 指定 runner の初回実行は Pegasus dispatch の `qstat -Q` preflight failure、rc=16、child 未起動。
- 同じ `tools.run_tests` runner の fallback 実走では、対象3ファイルの除外なし走行が `588 passed, 1 failed, 6 errors`。
- failure は未コミット HEAD 比較の既存 tripwire、errors は read-only `.git/.agents` による candidate fixture 作成失敗。
- 既知の7 nodeid を除外した最終走行は `587 passed`、rc=0。

除外対象は `test_current_repository_snapshot_exactly_matches_head`、candidate freeze 系5件、`test_repository_candidate_uses_real_s8c_budget_module` です。C06 変更関連テストは実走で pass しています。

静的波及:

- production caller は同一 evidence module の `_evaluate_undefined` と `PredicateRegistry.evaluate_all`。
- C06 共有 fixture は `TOKEN_ONLY_C06_BUDGET`、ratified fixture、supervisor fixture、current snapshot、candidate commit fixture。
- `DECIDER_VERSION` は preregistration の activation、P3、trial registry、reflux 系テストが汎用参照。
- C03/C08 の evaluator、contract flag、negative-control、staged registryには変更なし。

親への申し送り:

- g10 record と6つのコード／テスト変更を同一 commit に含めてください。
- commit 後に unfiltered acceptance と `check_ai_provenance.py` を再実行してください。
- C06 reachability 検査の弱点は D533 裁定どおり scope 外のままです。