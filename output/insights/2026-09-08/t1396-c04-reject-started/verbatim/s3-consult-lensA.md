## 総括

C04 は単純な「3 件目なし」では赤になるが、呼出し位置・支配関係を見ないため、preflight 外や実行不能な呼出しでも構造受理される。  
また既存 HEAD snapshot は実ファイルを読む一方、`reject_started_trial` の動作を見ないため、関数本体を no-op にしても期待値を通る。これは brief の I3 を満たさない。  
一方、新しい負例は「3 件目の call edge 欠落」だけで赤になる単一理由であり、変更後の C04 受理集合は既存集合の部分集合になる。  
テストは実走していない。以下は静的検査結果である。

## 所見

### `reject_started_trial` が preflight にあることを判定していない

file:line: [s8c_preregistration_evidence.py:610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:610), [同:1384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:1384), [同:1486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:1486), [contract:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:175), [production:4602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/p3_autonomous_workload_trial.py:4602)

なぜ破れるか: `_ReachabilityExplorer` は `main` から may-reach な全 call を集合化し、C04 はその集合に target があるかだけを見る。契約の「`run_trial preflight`」や呼出し順序は検査しない。したがって、現行の 4602 行目から call を削除して `record_trial_start_once()` 後へ移しても target は残る。重複 trial では 4695 行目の最終防御が先に raise するため、移動後の call は実際には実行されない。また `_live_nodes` は `if`/`while` の literal 判定しか特別扱いせず、`False and reject_started_trial()` のような短絡死コードも call witness になる。C09 は unknown branch を witness とすることを明記している [test:2330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2330) が、C04 契約には同じ緩和の記載がない。プランの負例は call の削除だけなので、この移動・死コード軸を殺さない。

成果物影響: preflight 拒否前に attempt slot の予約・分類が 4633、4660 行目で記録され得るのに、C04 report は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のままとなり、attempt 台帳の値と「拒否機構が配線済み」という参照が食い違う。

重さ: **must-fix**

### 実 HEAD 正例は関数の実体ではなく exact path/name までしか証明しない

file:line: [s8c_preregistration_evidence.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:294), [同:880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:880), [同:1393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:1393), [test:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:153), [test:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:282), [trial_registry.py:4796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/trial_registry.py:4796)

なぜ破れるか: resolver は exact module の top-level 関数定義があり、その関数への call が解決できれば記録するが、callee 本体は評価しない。`trial_registry.reject_started_trial` の 4796–4831 行を `pass` に置き換えても、planned evaluator、planned missing-call negative、current HEAD reason snapshot はすべて同じ構造結果になる。snapshot 自身も「同じ evaluator を使うので resolver mutation の kill 根拠ではない」と明記している [test:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:158)。したがって P1-c の「既存 snapshot で実体を示せる」という主張と brief I3 は成立しない。

成果物影響: no-op 化されると重複 launch は attempt slot の予約・分類後に 4748 行目の最終 start-once 防御で初めて止まり、attempt 台帳を消費する一方、C04 report の値は変わらない。現時点の certified 選択自体は、C04 が元々 `SATISFIED` を返さないため false のまま。

重さ: **must-fix**

### 追加予定の registry 存在検査は独立した拒否層にならない

file:line: [s2-plan.md:32](/home/SFC/tanab/.claude/jobs/596d8474/tmp/dev-wave-t1396-c04-reject-started/artifacts/t1396-c04-reject-started/s2-plan.md:32), [s8c_preregistration_evidence.py:965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:965), [同:1045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:1045)

なぜ破れるか: import symbol と module attribute のどちらも、resolver は対象関数が resolver 側 `_functions()` に存在するときだけ target を返す。したがって先行する `_declared_call(...reject_started_trial)` が真なら、後段の `_functions(registry)` 存在検査は必ず通る。定義欠落時は先行層の `crash-policy-cell-partial` で既に return し、`restart-guard-absent` には到達しない。プラン自身の 51 行目の認識どおりである。

成果物影響: 受理集合・report・台帳の値は変わらず、追加検査に独立した観測効果はない。

重さ: **nit**

## scope 外の real 所見

C04 契約の `field_paths` は `trial_lifecycle.started_once` と `trial_lifecycle.restart_forbidden` を要求する [contract:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:170) が、`_evaluate_c04` はこれらを一切読まない。実体は state 定義 [trial_registry.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/trial_registry.py:403)、start 時の設定 [同:4780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/trial_registry.py:4780)、restart 禁止時の更新 [同:4853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/trial_registry.py:4853) に存在するため、架空ではなく現在の lifecycle 機構との契約不一致である。

ただし D1292/T-1396 は 3 本目の reachable target 追加に限定されており、state transition の machine-checkable 範囲まで今回へ入れるのは scope 拡張になる。裁定パッケージ候補は「C04 の machine-checkable claim を call reachability に限定するのか、宣言済み lifecycle field の状態遷移まで含むのか」である。放置時は state 更新が失われても C04 report が変化せず、重複拒否・attempt 台帳と証拠参照が乖離する。

## プランと brief への同意点

- hard-coded target の名前と owner path は、契約の 3 件に名前上 1 対 1 で対応する。`mark_experiment_indeterminate`、`forbid_trial_restart`、`reject_started_trial` の組合せ自体は正しい。
- 新負例は単一理由である。call 削除後も `main -> run_trial`、先行 2 target、registry の両定義、`probe.declared_paths` は残るため、最初に変わる判定は 3 本目の `_declared_call` だけで、reason は `crash-policy-cell-partial` になる。後段存在検査は通過可能な入力のままである。
- 受理集合は緩まない。evaluator は既存 2 target に 3 本目を AND し、registry 検査も追加するため新集合は旧集合の部分集合である。`TOKEN_ONLY_C04` の直接参照は C04 branch [test:1203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:1203) に閉じ、parametrize 読者も identifier ごとに別 branch を選ぶため、C01/C09/C12 の負例は変更されない。
- literal dead branch・nested scope・entrypoint cut・test-only path・unimported decoy は既存 controls [test:2163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2163)、[同:2351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2351)、[同:2383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2383)、[同:2437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2437) と共通 resolver により塞がれる。module 再束縛・local shadow・alias decoy も resolver の exact binding 規則を通らない。新対象固有の別穴は、上記の位置非拘束と callee 無検査である。
- 親 probe の「現行 HEAD で 3 本目は解決する」という局所結論は妥当である。production は module import、preflight helper、exact registry 定義を持ち、追加予定の存在検査も現行 HEAD では通る。ただしこの probe は変更後 evaluator の実装検査ではなく、current snapshot の期待値据置きを予測する根拠にだけ限定すべきである。