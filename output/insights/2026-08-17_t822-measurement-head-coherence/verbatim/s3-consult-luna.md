静的レビューのみ実施。必読の brief と段 2 plan は読了し、pytest は実行していない。

### 所見 1: acceptance 出力と receipt pin の閉包が plan で不足している

判定: real

所見: `AcceptanceSummary` の直接 consumer はほぼ CLI とテストだけだが、receipt bytes には独立した parser、verifier、将来 consumer、golden がある。

根拠 (file:line):

- [`trial_registry.py:224`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:224)、[`trial_registry.py:2721`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2721)、[`trial_registry.py:2763`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2763)
- [`s8c_acceptance_receipt.py:33`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:33)、[`s8c_acceptance_receipt.py:49`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:49)、[`s8c_acceptance_receipt.py:245`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:245)、[`s8c_acceptance_receipt.py:289`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:289)
- [`s8c_acceptance_receipt.py:25`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:25)、[`s8c_acceptance_receipt.py:227`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:227)
- [`test_reflux_originless_compatibility.py:234`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_reflux_originless_compatibility.py:234)、[`test_trial_registry.py:824`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:824)、[`test_trial_registry.py:2213`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:2213)
- [`layer3_report.py:549`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/layer3_report.py:549) は s8c receipt の future consumer。`tools/dev_wave_land.py:632` は別形式の wave receipt であり、この receipt の consumer ではない。

識別子検索では、live な `non_certifying_reason_codes` pin は parser、writer、receipt tests、originless baseline に集約され、`arm_binding` は `AcceptanceSummary` と CLI/test に限られる。追加の実行 consumer は見つからなかった。

影響: A が内部変数だけを追加し、receipt v1、`AcceptanceSummary`、`_summary_dict` を変えなければ既存 output は保てる。一方、C の arm evidence を receipt row に追加すると exact key 検査で拒否される。さらに writer は origin 時だけ `origin_terminal_projection` を trial row に追加する一方、parser の exact trial key 集合には含めておらず、既存の writer/parser 不整合もある。

提案: A は common head を内部検査に限定する。C の証拠は report/journal bytes に置き、receipt v1 の key 集合を増やさない。origin projection の不整合は T-822 に黙って混ぜず、別修正または receipt schema revision として扱う。

### 所見 2: A の mixed-head 負例は実行時間上の blocker ではない

判定: refuted

所見: 既存 fixture は初期 commit、manifest commit、registry commitを既に作る。A の負例で無関係な tracked file の commit を 1 回追加し、6 report を 2 head に分ける構成は、campaign artifact を作らずに済む。

根拠 (file:line):

- [`test_trial_registry.py:130`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:130)
- [`trial_registry.py:2505`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2505)
- [`trial_registry.py:2590`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2590)
- [`trial_registry.py:2093`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2093)

影響: `history_checked` は head ごとに履歴 walk を一度行うため、既存の 1 head 正例に対し 2 head 負例は walk が 1 回増える。ただし、追加は 1 commit と 2 head の履歴検査であり、実 campaign の生成量には比例しない。実測はしていないので時間を緑とは報告できない。

提案: A の負例はこの軽量形で閉じる。6 本それぞれに commit を追加したり、Layer-3 artifact を作る設計にはしない。

### 所見 3: originless の 2 node は偶然の fixture ではなく既存契約である

判定: real

所見: 段 2 の「P4 は全て `cells: []`」という親 brief の記述は誤りだが、no-build acceptance 成功の衝突自体は実在する。

根拠 (file:line):

- [`test_trial_registry.py:341`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:341)、[`test_trial_registry.py:580`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:580)
- [`test_reflux_originless_compatibility.py:51`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_reflux_originless_compatibility.py:51)、[`test_reflux_originless_compatibility.py:65`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_reflux_originless_compatibility.py:65)
- [`test_reflux_originless_compatibility.py:568`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_reflux_originless_compatibility.py:568)、[`test_reflux_originless_compatibility.py:607`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_reflux_originless_compatibility.py:607)

影響: `_bundle` は実際の `run_trial` を 6 回実行し、`do_build=False` の report が `assert_trial_registry_acceptance` を通ることを要求する。baseline は acceptance key 集合、理由語 2 件、trial row 集合を固定している。Layer-3 必須化でこの成功を単に golden 更新することは、既存契約の反転になる。

提案: B は originless 方針の裁定が出るまで land 不可とする。fixture を build-backed に育てるだけでは、旧 no-build acceptance 契約を同時には保存できない。

### 所見 4: B には Layer-3 以前に production positive がない

判定: real

所見: 正式 holdout は `rr80` と `rr20` だが、production producer の閉集合は `ycsb-a/b/c` だけである。

根拠 (file:line):

- [`trial_registry.py:51`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:51)
- [`p3_autonomous_workload_trial.py:188`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/p3_autonomous_workload_trial.py:188)
- [`autonomous_trial_completeness.py:2271`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/autonomous_trial_completeness.py:2271)
- [`p3_autonomous_workload_trial.py:2371`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/p3_autonomous_workload_trial.py:2371)
- [`test_p3_autonomous_workload_trial.py:5166`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_p3_autonomous_workload_trial.py:5166)

影響: acceptance から chain を呼ぶと、現在の正式 6 report は producer-supported workload 検査で失敗する。テストだけが `WORKLOADS` を monkeypatch しており、これは production positive ではない。

提案: B の前に、正式 workload の production 支持と build-backed 6 report fixture を別単位で用意する。`do_build=True` と `cells` の cardinality は別の受理方針として明記し、chain 呼び出し必須化と混ぜない。

### 所見 5: B の fixture 移植案は恒真化とテスト時間を過小評価している

判定: real

所見: 段 2 が参照する `test_layer3_report.py` の fixture は、fresh rebuild を persisted report そのものに差し替えている。実 chain の positive にはならない。

根拠 (file:line):

- [`test_layer3_report.py:944`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_layer3_report.py:944)、[`test_layer3_report.py:965`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_layer3_report.py:965)、[`test_layer3_report.py:973`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_layer3_report.py:973)
- [`autonomous_trial_completeness.py:2100`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/autonomous_trial_completeness.py:2100)
- [`test_autonomous_trial_completeness.py:2168`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_autonomous_trial_completeness.py:2168)、[`test_autonomous_trial_completeness.py:2296`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_autonomous_trial_completeness.py:2296)
- [`test_trial_registry.py:1093`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:1093)、[`test_trial_registry.py:1111`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:1111)

影響: 実 positive は lock、WAL、persisted report、admission を生成し、chain は fresh WAL rebuild を行う。6 trial 用に複製すると、現在の軽量 JSON fixture より大幅に重くなる。partial の既存 acceptance も zero-cell と fake one-cell であり、11 node を単純置換する作業量ではない。

提案: 実 fixture は `test_autonomous_trial_completeness.py` の `_layer3_campaign` 型を基礎に、専用の少数 positive node に限定する。`test_layer3_report.py:944` 型の no-op verifier は使わない。partial policy と build positive を別 wave に切る。

### 所見 6: T-1279 が B を直接 block するという懸念は誤り

判定: refuted

所見: `assert_campaign_layer3_chain` の fresh rebuild は `generated_from_head` を明示指定するため、repo 外 campaign で `_git_head()` を呼ばない。

根拠 (file:line):

- [`autonomous_trial_completeness.py:2100`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/autonomous_trial_completeness.py:2100)
- [`layer3_report.py:162`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/layer3_report.py:162)
- [`layer3_report.py:511`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/layer3_report.py:511)
- [`layer3_report.py:554`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/layer3_report.py:554)

影響: plan 通り acceptance から `assert_campaign_layer3_chain` を呼ぶだけなら、[T-1279] の `_git_head` defect には到達しない。`layer3_report.py` を編集する必要もない。

提案: explicit `generated_from_head` を維持し、repo 外 campaign の chain fixture でその経路を確認する。acceptance から `build_report` を引数なしで直接呼ぶ変更だけは禁止する。

### 所見 7: C09 の実名修正は正しいが、hash closure の説明が不足している

判定: real

所見: `_evaluate_c09` は `accept_trial` を lookup するが、実コードの entrypoint は `assert_trial_registry_acceptance` である。修正後は contract bytes だけでなく freeze generation と evaluator snapshot に波及する。

根拠 (file:line):

- [`s8c_preregistration_evidence.py:459`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_preregistration_evidence.py:459)
- [`s8c_preregistration_evidence_contract.v1.json:339`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:339)
- [`test_s8c_preregistration_predicates.py:109`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_preregistration_predicates.py:109)
- [`test_s8c_preregistration_predicates.py:395`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_preregistration_predicates.py:395)
- [`test_s8c_preregistration_core.py:1153`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_preregistration_core.py:1153)
- [`s8c_preregistration.py:1482`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_preregistration.py:1482)
- [`s8c_preregistration.py:1863`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_preregistration.py:1863)

影響: contract の C09 だけを変えて frozen hash test を更新しないと赤になる。hash test だけ更新して freeze record を更新しなければ、current tip の `validate_condition_freeze_at` が record-contract mismatch になる。さらに C09 snapshot は旧 `UNSATISFIED` から `EVIDENCE_UNDEFINED` へ変わり、token-only fixture の関数名も変える必要がある。`accept_trial` は C02、C03、C08、C10 相当の contract 記述にも存在するため、全置換すると P3 と他 predicate の bytes まで変わる。

提案: C09 の object だけを実名化し、全置換しない。token-only C09 fixture、snapshot、current hash を更新し、既存 generation を壊さない新 generation、ruling reference、必要なら `DECIDER_VERSION` bump を同じ freeze 手順で用意する。

### 所見 8: P3 は arm 検査を無意味にはしない

判定: refuted

所見: `c02-arm-binding-unproven` を残したままでも、宣言と異なる arm-dependent artifact を拒否する fail-closed integrity gate には意味がある。これは certifying の発行とは別である。

根拠 (file:line):

- [`trial_registry.py:223`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:223)、[`trial_registry.py:229`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:229)
- [`s8c_acceptance_receipt.py:275`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:275)、[`s8c_acceptance_receipt.py:227`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:227)
- [`s8c_preregistration_evidence.py:623`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_preregistration_evidence.py:623)

影響: C が本物の capability digest を検査しても、v1 receipt は `certifying=false`、`arm_binding="declared-only"`、必須理由 2 件のままでよい。逆に `executed_arm = binding.arm` のような往復コピーは恒真であり、C を閉じたことにならない。

提案: C の当面の成果を「非認証 receipt に対する arm mismatch rejection」と定義する。実走 authority が確定するまで `arm_binding` と mandatory reason を変更せず、C02 の machine-checkable 昇格は別 freeze wave にする。

### 所見 9: A のみ land して T-822 完了とするのは台帳上不正確

判定: real

所見: A、B、C は `trial_registry.py` を共有し、B と C は producer 面も共有する。所有 file は素集合ではない。

根拠 (file:line):

- [`s2-plan.md:227`](/home/SFC/tanab/.claude/jobs/6b9ef1ad/tmp/t822/s2-plan.md:227)、[`s2-plan.md:233`](/home/SFC/tanab/.claude/jobs/6b9ef1ad/tmp/t822/s2-plan.md:233)
- [`brief.md:71`](/home/SFC/tanab/.claude/jobs/6b9ef1ad/tmp/t822/brief.md:71)
- [`trial_registry.py:2408`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2408)

影響: A は独立した narrowing として land できるが、親 brief が要求する 3 件の受入保証を閉じていない。親 worklog に `[T-822] 完了` とだけ記録すると、B の originless/production blocker と C の前提欠落を隠す。

提案: `T-822-A` を完了、親 `T-822` は partial、B は production-positive と裁定待ち、C は arm authority 設計待ちとして記録する。実務上は A → B 前提整備 → B gate/C09 freeze → C の順に分けるのが閉じた単位である。

## 総括

A は receipt v1 の形を変えずに実装でき、mixed-head fixture のコストも限定的である。  
親 brief の P4 は誤りだが、originless no-build acceptance という既存契約は実在する。  
B は production positive、originless 裁定、非恒真な build-backed fixture が揃うまで着地不能である。  
T-1279 は提案された call chain には到達しないため、B の直接 blocker ではない。  
C は P3 下でも有用だが、arm authority と freeze/contract 更新なしに完了扱いできない。