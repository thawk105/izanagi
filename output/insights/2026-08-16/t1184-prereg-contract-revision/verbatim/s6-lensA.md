## 総括

静的レビューの結論は **NO-GO** です。受理集合そのものの拡大や fail-open は見つかりませんでしたが、C11 の契約が実在しない識別子を要求し、評価器も契約上の到達関係を検査していません。加えて、診断理由と境界テストに規律 3 上の穴があります。pytest は実走しておらず、「緑」とは判定していません。

[severity: must-fix]  
[攻撃シナリオ] C11 の 3 入口で `_validate_generation_budget(generations)` を `_validate_generation_budget(2)` に変え、実引数を無検査にしても、評価器は呼び出し名しか見ないため終端の `EVIDENCE_UNDEFINED` まで到達する。同様に `validate_planner_payload()` から `_validate_critic_projection()` の呼び出しを削除しても、関数定義名を残せば検出されない。契約が要求する `main.generation_cap`、`run_trial.generation_cap`、`_run_workload.generation_cap` は実装に存在せず、実在するのは `args.max_generations` と `generations` である。  
[根拠] `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:419-441`、`orchestrator/campaign/s8c_preregistration_evidence.py:521-555`、`orchestrator/campaign/p3_autonomous_workload_trial.py:2279-2282`、同 `:2726-2731`、同 `:3203-3204`、同 `:3232-3233`、`orchestrator/campaign/s8c_generation_projection.py:795-802`。  
[成果物影響] 現在は全評価器が `SATISFIED` を返さないため certified 受理集合は直ちには広がらない。しかし g3 が実在しない field path と未検査の reachability を証拠契約として凍結し、C11 の材料レポート・試行台帳が「どの実引数と consumer edge を検査したか」を偽って参照する。将来の充足終端追加時には、そのまま受理集合拡大へ接続する。  
[提案] field path を実在する `args.max_generations` / `generations` に直し、評価器で validator の実引数、`main -> run_trial -> _run_workload`、`apply_critic_feedback -> planner_projection`、`validate_planner_payload -> _validate_critic_projection` を検査する。定数引数への差し替えと内部 edge 切断を負の対照へ追加する。

[severity: should-fix]  
[攻撃シナリオ] workload supervisor blob を削除すると、C01・C04・C11・C12 は `UNSATISFIED` ではなく `EVIDENCE_UNDEFINED/workload-supervisor-absent` を返す。それにもかかわらず規範本文は、機械検査対象になった 6 条件が「証拠が欠けていれば不充足を返す」と一般化している。これは現 HEAD 一点の M2 vector を一般則へ広げた記述である。  
[根拠] `docs/phase3-8c-preregistration.md:252-259`、`orchestrator/campaign/s8c_preregistration_evidence.py:412-415`、同 `:442-445`、同 `:517-520`、同 `:564-567`、`/work/1/SFC/tanab/dev-wave-jobs/t1184/artifacts/brief.md:76-90`。  
[成果物影響] g3 の `normative_body_sha256` が、実際の activation report status と異なる説明を凍結する。受理集合は不変だが、材料レポートと試行台帳で `UNSATISFIED` と `EVIDENCE_UNDEFINED` の意味を誤って説明する。  
[提案] 「6 件の登録済み負の対照では mutation 側が条件別 `UNSATISFIED` を返す」と限定する。missing blob 全般まで一般化しない。

[severity: should-fix]  
[攻撃シナリオ] 評価器を持たない C02 を `machine_checkable: true` にすると、原因は evaluator registry の欠落なのに `commit-blob-read-error` と報告される。blob 読取失敗を調査しても真因へ到達できない。  
[根拠] `orchestrator/campaign/s8c_preregistration_evidence.py:691-706`、`orchestrator/tests/test_s8c_preregistration_predicates.py:599-612`。  
[成果物影響] fail-closed は維持されるが、activation report、材料レポート、試行台帳の reason code が虚偽になり、次の修正を blob 復旧へ誤誘導する。  
[提案] `machine-evaluator-absent` など閉じた専用 reason code を追加し、`contract-machine-evaluator` を個別に写像する。

[severity: should-fix]  
[攻撃シナリオ] C10 の raw-response hash ではなく、別の必須 field、`read_and_verify_bytes` 呼び出しを壊しても同じ `cross-binding-verifier-incomplete` になる。C04・C09・C12 も複数 sub-check を同じ reason code に畳んでおり、reason code だけでは名指しの負の対照が発火した証拠にならない。  
[根拠] `orchestrator/tests/test_s8c_preregistration_predicates.py:440-477`、同 `:530-542`、`orchestrator/campaign/s8c_preregistration_evidence.py:446-470`、同 `:496-509`、同 `:577-591`。  
[成果物影響] 現在の各 fixture は単一箇所だけを壊しており過剰決定は見つからなかったため、受理集合への影響はない。一方、材料レポート・台帳の reason code は、どの保証が破れたかを一意に説明できない。  
[提案] sub-check ごとに reason code を分けるか、少なくとも負の対照結果へ検出した sub-check ID を構造化して残す。

[severity: should-fix]  
[攻撃シナリオ] C08 の `consumer_requirement.proof` を exact parent set `{P}` から単なる ancestry 検査へ弱めても、`test_c03_c08_contract_uses_two_stage_binding_without_self_reference` は field 集合しか確認しないため通る。  
[根拠] 現契約の正しい exact-parent 文は `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:329-336`。境界テストは `orchestrator/tests/test_s8c_preregistration_predicates.py:676-698` で、親集合規則を assert していない。  
[成果物影響] 現在の C03/C08 は `machine_checkable: false` なので即時の受理集合は不変。ただし consumer 配線後、祖先 commit を発効 commit の代用として受理し、manifest と measurement の proof chain を広げうる。  
[提案] C08 の exact-parent 規則を prose ではなく構造化契約 field にし、`parents(C) == {P}` を境界テストで固定する。構造化変更を見送るなら、最低限 ancestry-only 文への変異が失敗するテストを追加する。

確認できた防壁は次のとおりです。

- `SATISFIABLE_CONDITION_IDS` は空で、評価器に `SATISFIED` を返す経路はありません。
- `activation_report_at()` は 12 件すべての exact `SATISFIED` を要求し、`effective_at()` と受入 consumer も再導出結果を使うため、`EVIDENCE_UNDEFINED` と `UNSATISFIED` はともに fail-closed です。
- 6 param はすべて baseline が `EVIDENCE_UNDEFINED`、mutation が別の `UNSATISFIED` 期待値で、恒真ではありません。
- loop は `exercised == 6` を assert しており、0 回恒真化は塞がれています。
- diff に skip、xfail、approx、`assert True` 相当の弱化はありません。
- `machine_checkable: true` の 6 条件と評価器 6 本は双方向一致しています。
- 現契約には裸の `prereg_commit`、manifest 自己 digest、`is-ancestor` 代用はなく、C08 は exact `{P}` を要求しています。
- `_evaluate_c11` は `cap < 2` のままで、exact `2` へ狭められていません。
- 条件 3/8 の consumer が未配線であることは文書に明記されています。