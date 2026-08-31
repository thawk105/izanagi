## 総括

結論は「現行scopeのままでは、T-1874全体の実装planは受理不可」です。

発効判定へ `section5_value_violations == ()` を追加し、`DECIDER_VERSION` を v7へ上げ、g12を発行する部分は実装可能です。一方、production consumerは既存schemaだけでは構成できません。

配置候補は親brief P1を狭めた次の位置です。

`p3_autonomous_workload_trial.run_trial`  
→ 6個の terminal report  
→ `trial_registry.assert_trial_registry_acceptance`  
→ manifest/report/attemptの検査完了  
→ `s8c_result_judge.verify_floor_bytes`  
→ `judge`  
→ `publish_result_table`  
→ acceptance receipt

具体的には [trial_registry.py:5978](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:5978) から [trial_registry.py:5997](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:5997) のattempt/lifecycle検査後、receipt生成 [trial_registry.py:6125](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:6125) より前です。単一trialしか持たないsupervisor内や、authorityを捨てた `AcceptanceSummary` 返却後ではありません。

ただし、その位置にも既存 judge が要求する `6 × n` 観測、H1/H2別パラメータ、raw-value attestationを供給できる既存schemaがありません。新schema、judge変更、judge結果の独自合成のいずれかが必要になり、いずれも今回の制約に抵触します。

## 実アンカー

- §5 parserは違反を列挙済みです。[s8c_preregistration.py:771](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:771) で値を検査し、[s8c_preregistration.py:1042](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:1042) で `section5_value_violations` を保持します。

- 現行の発効連言はfreeze、decider、一括FILLED、12 predicateだけです。[s8c_preregistration.py:1925](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:1925) と [s8c_preregistration.py:1951](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:1951)。違反空集合は連言に未参加です。

- `ActivationReport` の既存field集合は [s8c_preregistration.py:243](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:243) です。D534に従いfieldは増やさず、発効式の内部値として違反空集合を使えます。

- 発効digestの正本は `_activation_report_digest` と `require_effective_preregistration` です。[s8c_preregistration.py:2130](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:2130) から [s8c_preregistration.py:2166](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:2166)。

- supervisorは1回の `run_trial` につき1 reportを作り、formal runでは `cells` は最大1個です。[p3_autonomous_workload_trial.py:3523](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:3523) と [trial_registry.py:1618](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:1618)。したがってsupervisor内では6 cellをjudgeへ渡せません。

- manifestの既存schemaはexact 6 trialですが、保持するのは `trial_id / arm / holdout / campaign_id / generations` だけです。[trial_registry.py:110](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:110)、[trial_registry.py:261](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:261)、[trial_registry.py:769](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:769)。judgeが要求する `n / schedule / source_binding / swapped_mapping` はありません。

- acceptanceはexact 6 reportを同時に保持し、manifest trial集合、report bytes、journal、P/C、launch admissionを検査します。[trial_registry.py:5551](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:5551) から [trial_registry.py:5717](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:5717)。これはproduction callerを置ける唯一の既存集約点です。

- P2のsource bindingは次の独立読取なら成立します。

| judge側入力 | authority |
|---|---|
| `params.source_binding` | 発効commitから再計算した `EffectivePreregistration.report_digest_sha256` |
| `manifest.source_binding` | 6 reportそれぞれの永続化済み `launch_admission.activation_report_digest_sha256` |
| 一致条件 | 6 report間で全一致し、fresh発効digestとも一致 |

  report側digestは [p3_autonomous_workload_trial.py:3548](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:3548) で保存され、acceptanceはfresh capability由来の期待値と [trial_registry.py:5702](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:5702) で再照合します。同じfresh値から両入力をその場で生成する案は却下です。

- 既存 judgeは単一のscalar `_ContrastParams` しか受けません。[s8c_result_judge.py:118](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:118)、[s8c_result_judge.py:1947](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:1947)。その1個の `n / delta_min / sd_max` がH1とH2の両方へ使われます。

- judgeは `6 × n` schedule行を要求します。[s8c_result_judge.py:376](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:376)。各観測はraw値、correctness、trace無効化、raw-value attestationを必要とします。[s8c_result_judge.py:520](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:520)。

- 対してproduction supervisorは `replicate_index == 0` のslotだけを選びます。[p3_autonomous_workload_trial.py:1299](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:1299)。acceptanceもmanifestごとにreplicate 0だけを許し、追加replicateを拒否します。[trial_registry.py:3471](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:3471)。

- attemptの `primary_value` はthroughputではなく累積bench wall秒です。[p3_autonomous_workload_trial.py:3616](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:3616)。judgeの固定単位は `throughput_tps` です。[s8c_result_judge.py:40](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:40)。

- 既存3 entrypointにはproduction callerがありません。射影対象内での呼出しは `test_s8c_result_judge.py` だけです。evidence contract C07の自己完結した到達記述 [s8c_preregistration_evidence_contract.v1.json:267](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:267) はproduction reachabilityの証拠になっていません。

## Plan

1. 発効判定の閉包だけは次の形で実装する。

   - [s8c_preregistration.py:51](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:51) を `s8c-decider/v7` へ変更する。
   - [s8c_preregistration.py:1925](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:1925) 付近で `value_valid = contract is not None and not contract.section5_value_violations` を導出する。
   - [s8c_preregistration.py:1951](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:1951) の既存連言へ `and value_valid` を追加する。`ActivationReport` fieldは変更しない。
   - [docs/phase3-8c-preregistration.md:281](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/docs/phase3-8c-preregistration.md:281) の発効定義を更新する。特に「欄別型検証は発効対象外」という [docs/phase3-8c-preregistration.md:287](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/docs/phase3-8c-preregistration.md:287) は新しい連言と矛盾するため修正が必要。
   - consumerが閉じた同一commitでのみ、[s8c_preregistration.py:2035](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:2035) の `prepare_revision` からg12をexclusive-createする。g1からg11は改変しない。

2. 発効版§5値の読取は、発効commitのblobから行う。

   - [s8c_preregistration.py:771](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_preregistration.py:771) のtable parserを再利用し、対象欄のcanonical JSON値を返すprivate commit-scoped accessorへ整理する。
   - worktree値やcaller提供mappingは使わない。
   - H1とH2それぞれについて既存 `_ContrastParams` を構築し、fresh発効digestを `source_binding` とする。
   - ただし、2個のparamsを既存 `judge` へ正しく渡せないため、この段階をconsumer実装の停止点とする。

3. production callerを実装できる前提が揃った場合のみ、`trial_registry`へ配置する。

   - [trial_registry.py:5978](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/trial_registry.py:5978) のattempt acceptanceとsnapshot固定後にprivate C07 consumerを呼ぶ。
   - manifest由来: exact 6 trial、holdout、arm、campaign、manifest hash、P/C。
   - report由来: 各cellのG1/G2成果、proposal、final G2 variant、永続化済み発効digest。
   - attempt由来: slot、schedule row hash、terminal status、report hash、observation hash。
   - これらを相互照合してから `verify_floor_bytes -> judge -> publish_result_table` を呼ぶ。
   - [s8c_result_judge.py:29](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/orchestrator/campaign/s8c_result_judge.py:29) の3 entrypoint、judge schema、table schemaは変更しない。
   - 現状はschedule/observation/H別paramsを投影できないため、この項目は実装不可。

4. consumerが実在してから証拠契約と凍結を更新する。

   - C07のconsumer requirementをjudge自身から `trial_registry.assert_trial_registry_acceptance` の実際のcaller chainへ変更する。
   - `p3_autonomous_workload_trial.run_trial -> terminal reports -> trial_registry.assert_trial_registry_acceptance -> verify_floor_bytes -> judge -> publish_result_table` を記録する。
   - invariantのfunction pinへproduction callerを追加する。
   - live doc、evidence contract、core/evaluator/projection、v7、g12を同一commitへ束縛する。

## 受理と拒否

受理できるもの:

- `section5_value_violations == ()` の発効連言追加。
- `ActivationReport` field集合を変えないv7変更。
- 発効commitからの§5再読。
- fresh発効digestと、6 reportに永続化されたlaunch-admission digestの独立照合。
- exact 6 reportとattempt snapshotが揃った `trial_registry` 内へのcaller配置。
- 既存judgeと既存3表publisherの直接利用。
- g12だけのexclusive-createとg1からg11の歴史維持。

拒否するもの:

- supervisorの単一report内で6 cellを捏造する案。
- report順からscheduleを後付け生成する案。
- G1/G2を統計上の反復 `n` と読み替える案。
- attemptのbench wall秒をthroughputへ転用する案。
- report値からraw-value attestationを同じcaller内で生成する恒真束縛。
- fresh発効digestから `params.source_binding` と `manifest.source_binding` の両方を生成する案。
- H1/H2 paramsが同じだと未裁定で仮定する案。
- judgeを2回呼び、private `_JudgeResult` を独自合成する案。
- `_ContrastParams` をholdout mappingへ変える案。
- manifest、report、attempt registry、result tableの新schema追加。
- `s8c_result_judge` のロジック複製。

## テスト

read-onlyのため、以下は候補nodeであり未実走です。緑とは報告しません。

- `orchestrator/tests/test_s8c_preregistration_core.py`

  - 新規 `test_section5_value_violations_keep_activation_false`
  - 新規 `test_empty_section5_value_violations_preserve_full_conjunction`
  - 既存 `test_matching_decider_version_preserves_activation_conjunction`
  - `test_decider_version_binds_cross_module_semantics_to_v6` をv7 pinへ更新
  - 新規 `test_activation_report_field_set_is_unchanged_by_value_gate`
  - 既存 `test_prepare_revision_is_exclusive_create`
  - current evidence hash pinを新しいcontract digestへ更新

- `orchestrator/tests/test_s8c_preregistration_invariant.py`

  - `test_candidate_freeze_matches_contract_and_generation_chain` でlatest g12を固定
  - 新規 `test_g1_through_g11_history_bytes_are_unchanged`
  - C07 function pinへproduction callerを追加
  - C07 evidence contractがsupervisor、registry、既存3 entrypointを同一reachability chainとして持つことを固定
  - 既存 `test_living_doc_section5_value_violations_are_empty` は維持し、現行§5未記入かつ未発効も維持

- `orchestrator/tests/test_trial_registry.py`

  - 既存 `test_p5_six_complete_terminal_reports_pass_acceptance`
  - 既存 `test_attempt_acceptance_rejects_unmanifested_replicate_slot`。これは現行blockerの直接証拠
  - 新規 `test_acceptance_rejects_nonunanimous_report_activation_digests`
  - 新規 `test_acceptance_binds_report_digest_to_fresh_effective_digest`
  - 新規 `test_acceptance_rejects_missing_exact_n_schedule_rows`
  - 新規 `test_acceptance_rejects_report_attempt_observation_mismatch`
  - 新規 `test_acceptance_publishes_exactly_three_create_only_tables`
  - 新規 `test_acceptance_receipt_is_not_issued_when_result_publication_fails`
  - 新規 `test_result_tables_are_rolled_back_when_receipt_publication_fails`

- `orchestrator/tests/test_s8c_result_judge.py`

  - 既存 `test_generation_result_tables_use_actual_and_expected_g2_variants`
  - 既存 `test_source_binding_mismatch_is_indeterminate_not_a_new_status`
  - 既存 `test_generation_outcome_requires_exact_generation_sequence`
  - 既存 `test_publish_creates_three_separate_tables_from_independent_six_cell_set`
  - 既存 `test_publish_is_create_only_and_does_not_overwrite_bytes`
  - judge/schemaを変更しないため、これらは回帰検査として使う。

## Scope外・未解決

1. H1/H2別params

   §5はH1/H2別の値を許しますが、judgeは1個のscalar `_ContrastParams` しか受けません。H1/H2で `n / delta_min / sd_max` が異なる正当な発効値を、既存judgeだけで6 cellの1結果へ反映する方法がありません。judge schema変更、§5でH1/H2同値を要求する規範変更、またはjudge結果合成のいずれかが必要です。

2. 反復集合

   §5 validatorは `n >= 2` を要求しますが、現行formal attempt acceptanceは各manifest trialについて `replicate_index == 0` だけを受理し、追加replicateを拒否します。既存schemaではjudgeの `6 × n` 完全blockを構成できません。

3. 観測authority

   attempt terminalの `primary_value` はbench wall秒です。judgeが必要とするthroughput raw値とraw-value attestationは、report/attemptの既存受理schemaから独立に取得できません。report内のharness値をcallerがattestationへ包み直す案は恒真束縛なので却下です。

4. 出力とreceiptの原子性

   `publish_result_table` はrepository外の3 pathへcreate-only出力しますが、acceptance receiptはrepository内へ別トランザクションで作られます。3表成功後のreceipt失敗、またはreceipt成功後の3表失敗を単一の既存transactionで閉じる仕組みがありません。

以上から、発効連言だけを先行着地すると「発効し得るがproduction consumerへ到達できない」中間状態になります。T-1874を一変更単位で閉じる条件に反するため、現scopeでは実装開始せず、既存schemaのどのauthorityが `6 × n` throughput observationsとH1/H2別paramsを供給するかの追加裁定が必要です。