## 所見

1. 対象 `s2-plan.md:36`、`orchestrator/campaign/p3_s4_loop.py:1058-1090`、`orchestrator/campaign/p3_b4_wiring_probe.py:1464-1475`、`orchestrator/tests/test_p3_b4_raw_record_producer.py:149-160`。`default_cfg()` の未束縛化は既存 consumer に対して互換ではない。wiring probe は `cfg.bound_environment_contract.contract_sha256` を直読するため `None.contract_sha256` で停止し、raw-record fixture も同 field を `assert contract is not None` している。identity だけを読む `p3_b4_closed_critic.py:1984-1991` と `p3_b4_wiring_probe.py:1660-1663` は壊れないが、上記二経路は壊れる。成果物への影響: wiring-probe evidence を全 driver で発行できず、raw-record producer の fresh fixture 群が assembly 前に停止する。重大度: must-fix。

2. 対象 `orchestrator/campaign/p3_b4_launcher.py:147-174,527-556,596-609`、`s2-plan.md:59-63,117`。launcher は trigger だけを site projection し、base の `on_cfg/off_cfg` は legacy ID のまま context と sidecar に束縛する。一方、計画後の base `main` は PEGASUS_COMPUTE で `measurement_env="pegasus"` を加えた別 ID を `drive_iteration` の B4 gate に渡すため、launcher context の campaign ID と一致しない。これは残存リスクとして受容できる挙動ではなく、sanctioned base B4 compute route の既存 consumer 破壊である。成果物への影響: launcher は旧 ID の root に sidecar を書いた後、base iteration を campaign-ID mismatch で拒否し、Pegasus campaign を開始できない。重大度: must-fix。

3. 対象 `s2-plan.md:59`、`orchestrator/campaign/p3_s4_loop.py:1957-2017`、`orchestrator/tests/test_p3_exploration_namespace.py:665-714`。計画は site 解決を CLI 整合 gate `:1957-1974` の直後へ置くが、既存の coder build authority gate は `:2012-2013` にある。この順序では無 opt-in の base CLI が、本来の `BuildAdmissionError` より先に PEGASUS_LOGIN の `ExecutionGuardError` を返す。成果物への影響: coder authority の拒否境界と例外参照が変わり、`test_cli_authority_boundary_rejects_before_build_spy` の base case が赤になる。通常経路では authority gate 後、emit-context 経路では layout 導出前に個別解決すべきである。重大度: must-fix。

4. 対象 `s2-plan.md:67-85`、`orchestrator/tests/test_p3_exploration_namespace.py:1124-1222,1291-1379`、`orchestrator/tests/test_p3_b4_closed_critic.py:2868-2937`。テスト修正対象が `test_p3_s4_loop.py` に閉じており、別ファイルの直接 caller が漏れている。base case の `module.main()` と `module.run_one_iteration()`、および `L.drive_iteration()` はすべて新しい自動 site 解決へ到達し、この機体では login 拒否になる。成果物への影響: 少なくとも `test_driver_build_spy_receives_exact_run_context`、`test_iteration_public_entry_routes_runtime_layout_and_selector`、`test_public_b4_receipt_gate_accepts_live_certified_bound_receipt` が本来の sink/receipt 検査前に赤になる。重大度: must-fix。

5. 対象 `s2-plan.md:69-83`。追加テスト群は注入経路へ偏り、成功する自動経路 `_current_site()` → `_admit_env_contract()` → `_campaign_cfg_for_site()` を必須の正例として名指ししていない。`test_s4_other_identity_is_unchanged_and_compute_is_split` は `_campaign_cfg_for_site` が単に入力 cfg を返しても OTHER 部分が通り、post cfg の `bound_environment_contract is contract` も計画されていない。また compute の emit/run ID 一致は両経路がとも projection を省略しても成立する。成果物への影響: OTHER が未束縛のまま、または main の両経路がとも legacy namespace を使う実装をテストが受理しうる。自動解決の正例で exact contract object、post-bind field、compute marker、captured `run_campaign` cfg を同時に検査する必要がある。重大度: must-fix。

6. 対象 `orchestrator/campaign/p3_s4_loop_sort.py:69,192,262,331,340`。参照関係を追うと sort driver は `p3_s4_loop` の `quarantine`、`record_diff_reject`、`default_perf`、duplicate/state/digest helper を再利用するが、変更対象の `default_cfg`、`run_one_iteration`、`drive_iteration`、`main` は再利用していない。追加引数も keyword-only default 付きなので既存 positional caller の署名破壊はない。成果物への影響: sort の受理集合や campaign ID は今回の署名変更だけでは変わらない。重大度: nit。

## この機体で赤になるテストの一覧

以下は production 側だけを移植し、現行 `test_p3_s4_loop.py` の呼出しをまだ直していない場合の一覧である。いずれも `pegasus02` で `_current_site()` → `PEGASUS_LOGIN` → `_admit_env_contract()` 拒否へ到達する。`s2-plan.md:69` の注入修正を漏れなく実装すれば、このファイル内の残存赤はない。

- `orchestrator/tests/test_p3_s4_loop.py:591` `test_backoff_value_raw_canonical_source_and_genome_are_one_chain` — `run_one_iteration` の B4 gate 通過後に site 解決へ到達する。
- `:2469` `test_run_one_iteration_rechecks_mutated_nonintegral_value_before_genome_construction` — attribution/value 再検査より先に site 解決へ到達する。
- `:3502` `test_reflux_off_reject_keeps_wal_and_whiteboard` — `drive_iteration` の coder-domain gate 後に到達する。
- `:3600,3639` `test_sanctioned_cli_stdout_omits_red_detail_fields` — 両 `main` 呼出しとも CLI 整合 gate を通過する。
- `:4152` `test_b4_driver_rejects_bootstrap_claim_over_nonempty_admitted_history` — base parameter が helper `:3973` の `drive_iteration` から到達する。
- `:4162` `test_b4_true_bootstrap_reaches_synthesis_for_all_drivers` — base parameter が同じ helper 経由で到達する。
- `:4273` `test_m08_b4_drive_iteration_rejects_before_layout_and_state_progress` — B4 production-context gate より前に site 解決へ到達する。
- `:4439` `test_production_context_does_not_weaken_six_receipt_rejections` — receipt の各拒否条件より前に到達する。
- `:4541` `test_b4_bound_decision_reaches_synthesis_and_writes_exact_consumption` —正の B4 drive 経路で到達する。
- `:4613,4616` `test_b4_same_terminal_receipt_hash_is_consumed_at_most_once` — 初回、再利用拒否の両方で先に到達する。
- `:4726,4732` `test_b4_bootstrap_rejects_receipt_but_allows_none_to_reach_synthesis` — bootstrap receipt 判定より前に到達する。
- `:4751` `test_b4_no_build_stops_before_artifact_change_m12` — B4 no-build 拒否より前に到達する。
- `:4825` `test_b4_receipt_gate_precedes_fold_iteration_and_artifact_mutation` — receipt gate より前に到達する。
- `:5652,5691` `test_emit_context_and_run_iteration_share_manifest_campaign_identity` — emit と run の両 `main` 経路で到達する。
- `:5712` `test_main_emits_planner_context_from_new_state` — emit-context の layout 導出前に到達する。
- `:5731` `test_main_emits_planner_context_with_policy_hint` — 同じ emit-context 経路。
- `:5744` `test_main_emits_planner_context_with_cli_policy_hint` — 同じ emit-context 経路。
- `:5842` `test_drive_iteration_stops_before_running_when_reverse_exhausted` —入口 stop 判定より前に到達する。
- `:5915` `test_drive_iteration_recovers_real_wal_start_before_entry_stop` — WAL recovery と入口 stop より前に到達する。
- `:5948` `test_run_one_iteration_records_oversized_preflight_as_rejection` — preflight rejection より前に到達する。
- `:5986` `test_run_one_iteration_records_nonliteral_initializer_as_structured_rejection` — quarantine より前に到達する。
- `:6048` `test_run_one_iteration_preserves_outer_quarantine_rejection_order` — outer quarantine より前に到達する。
- `:6091` `test_inner_run_recovers_reject_start_before_writing_retry_start` — recovery より前に到達する。
- `:6128,6142` `test_drive_iteration_checkpoint_survives_across_calls` —両 iteration で到達する。
- `:6169` `test_drive_iteration_clean_no_build_skips_admitted_critic_digest` — no-build iteration へ入る前に到達する。

`test_m04_b4_marked_run_one_iteration_direct_call_requires_launcher` `:4235` は run-one の既存 B4 gate が先に拒否するため未到達、`test_drive_iteration_rechecks_mutated_nonintegral_value_before_entry_stop` `:5877` は coder-domain gate が先に拒否するため未到達、`:4780,4792,4794` の `main` は CLI 整合 gate が先に拒否するため未到達である。

## 親 brief への指摘

`env_contract.lookup(ENV_TAG)` と計画上の `_admit_env_contract(OTHER)` は production では同一 object を返す。`_SITE_ENV_TAGS[OTHER] == ENV_TAG`、`_lookup` は同じ `env_contract.lookup` の別名であり、activation snapshot の同じ registry entry を返す。`ident.bind_environment_contract` は `bound_environment_contract` だけを `replace` し、OTHER の `_campaign_cfg_for_site` は `search_config` 用 `replace` を通らない。したがって最終 cfg の通常 field 値と `search_config` object は移植前と同じで、`canonical_preimage` が runtime contract を含めないため現行 OTHER の ID は `8ee68c0c` / `95a32c3e` のままである。

`output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/campaign.lock:1` は現在の `default_cfg()` の preimage ではない。`build_admission` と backoff grammar version を持たない歴史的 lock であり、現行 golden は `test_p3_s4_loop.py:4185-4189` の二 ID である。親 brief `:38-40` の「0b53a387 を根拠に OTHER identity を検査する」という一般化は狭めるべきで、守るものは同じ入力 cfg の移植前後 bytes と、歴史的 directory/overlay/pin を書き換えないことの二つである。

親 brief `:62-65` の P4 provisional は段2の確認で supersede 済みである。`default_cfg` の既存 bind を残す案は compute で再 bind error になる一方、外す案には所見1の consumer 修正が必須であり、片方だけ採用できない。

実測前提はその他すべて裏が取れた。hostname は `pegasus02` で NQSV 証拠があり `PEGASUS_LOGIN`、Pegasus active contract は 2100 / `()` / `allow_resume=False`、対象 module は `replace` import 済みで `execution_guard` / `site_policy` 未 import、歴史的 directory も実在する。ただし「login node では raise」は `_admit_env_contract` へ到達した経路だけに限られ、CLI の先行 gate や未束縛 `default_cfg()` 自体には一般化できない。

## scope 外だが real な所見

- `p3_s4_loop_trigger_gating.py:475` 相当の `_assert_resume_allowed` を移植しないため、Pegasus contract の `allow_resume=False` は base loop 入口では強制されない。別 process が同じ compute campaign root を開けば WAL recovery、checkpoint、digest を更新できる。
- base loop は `CampaignSummary.execution_receipt` を caller-side provenance として永続化しない。`run_campaign` 内の検証は残るが、trigger driver と同じ追跡可能性は得られない。
- `p3_s4_loop_sort.py` は今回の署名変更では壊れない一方、driver 自身は依然として linux-baremetal の定数と契約を直接使う。sort の Pegasus 対応は別裁定が必要である。

## 総括

- OTHER の identity 不変そのものは実コードから証明でき、現行 golden ID も変わらない。
- 最大の欠陥は、P4 反転に伴う既存 consumer 更新と base B4 launcher の compute projection が計画から漏れていること。
- 対象テストファイルの hostname 依存 call は計画の注入範囲で覆えるが、別テストファイルの直接 caller と authority gate 順序は覆えていない。
- 段4では、scope を launcher、wiring probe、raw fixture、横断 namespace tests まで広げることを必ず裁定すべきである。
- pytest は実走しておらず、以上は静的検査結果である。