## 焦点走の集合への所見 (漏れの名指し)

- **real — 親の直接 grep 28 file は不完全。** 確認した集合は次のとおりです。

```text
test_auditor_gate.py
test_campaign.py
test_campaign_import_invariant.py
test_codex_agents.py
test_floor_pair_driver.py
test_hooks.py
test_layer3_report.py
test_p3_b4_closed_critic.py
test_p3_b4_launcher.py
test_p3_b4_material_report.py
test_p3_b4_proposal_binding.py
test_p3_b4_raw_record_producer.py
test_p3_b4_wiring_probe.py
test_p3_build_authority_cli.py
test_p3_exploration_namespace.py
test_p3_s4_loop.py
test_p3_s4_loop_job_contract.py
test_p3_s4_loop_sort.py
test_p3_s4_loop_trigger_gating.py
test_pytest_collection_config.py
test_real_repo_serialization.py
test_s1_direct_comparison.py
test_s6_sort_sweep.py
test_s8a_trigger_sweep.py
test_s8b_oracle_driver.py
test_sort_swo_oracle.py
test_trigger_gate_binding.py
test_update_acceptance_duration_ledger.py
```

  二段の実 consumer として次の2 fileが漏れています。

  - `test_p3_b4_admission_record.py`: `C.projection_sha256()` を呼びます（[test_p3_b4_admission_record.py:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_admission_record.py:332)）。その closure は変更ファイルの bytes を読むためです（[p3_b4_closed_critic.py:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_closed_critic.py:623)）。
  - `test_p3_b4_producer_auth_experiment.py`: 実 raw-producer 経路を呼びます（[test_p3_b4_producer_auth_experiment.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:352)）。raw producer も projection closure に変更ファイルを含めます（[p3_b4_raw_record_producer.py:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_raw_record_producer.py:987)）。

  放置影響: projection SHA・admission 参照・raw report 検証の回帰を焦点走が検出できません。

- **real — collection meta-test も漏れ。** 新 node 追加に反応する `test_acceptance_schedule_order.py`、特に `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` も焦点対象です（[test_acceptance_schedule_order.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_acceptance_schedule_order.py:660)）。

  放置影響: ledger coverage の分母増加を未検査のままにし、受入 scheduler の未知所要時間 node を増やします。

## meta-test と受入台帳

- **real — 新規 test は3 nodeを追加。** `_DRIVERS = base/sort/trigger` による parameterize なので（[test_p3_b4_proposal_binding.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:30)、[同:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:94)）、追加 node は以下です。

```text
...::test_registry_attempt_outside_analysis_manifest_rejects[base]
...::test_registry_attempt_outside_analysis_manifest_rejects[sort]
...::test_registry_attempt_outside_analysis_manifest_rejects[trigger]
```

  静的集計では対象 file は23→26 nodeです。

  放置影響: 全 collection の件数と ledger coverage 比率の分母が3増えます。

- **refuted — file集合・命名・件数を exact 固定する meta-test の更新は不要。** exact node-set 固定対象は8 suiteだけで、`test_p3_b4_proposal_binding.py` は含まれません（[test_update_acceptance_duration_ledger.py:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_update_acceptance_duration_ledger.py:364)）。全 collection 側は exact count ではなく90% coverage gateです（[test_acceptance_schedule_order.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_acceptance_schedule_order.py:696)）。

  放置影響: exact pin の値は変わりませんが、G5 の実走確認は別途必要です。

- **refuted — 新 node の台帳登録は必須ではない。** 現台帳にはこの test file の既存 nodeも0件です。consumer は未登録 nodeを `None` として許容します（[conftest.py:1571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/conftest.py:1571)）。また add-only の凍結 suite にも含まれません（[update_acceptance_duration_ledger.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/tools/update_acceptance_duration_ledger.py:21)）。

  放置影響: correctness や台帳既存値は変わらず、3 nodeが未知所要時間として scheduling されるだけです。

## 3 呼び手への波及

- **real — base/sort/trigger の3 bootstrapすべてへ意図どおり効く。** 共通 gate の呼び出しは base（[p3_s4_loop.py:2250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:2250)）、sort（[p3_s4_loop_sort.py:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop_sort.py:490)）、trigger（[p3_s4_loop_trigger_gating.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop_trigger_gating.py:970)）で同型です。

  放置影響: 3 driverすべての formal bootstrap 受理集合が manifest 201行へ縮小します。certified 選択の定義や既存 report 値は変更しません。

- **refuted — continuation への誤適用なし。** 3 loaderとも `b4_closed_critic_receipt_sha256 is None` の bootstrap 分岐でだけ新 gateを呼びます。receipt付き continuation はこの分岐を通りません。3 driver共通の正例もあります（[test_p3_b4_proposal_binding.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:357)）。

  放置影響: continuation の受理集合・receipt参照・checkpoint値は変わりません。

- **refuted — raw producer の `_manifest_row()` と冗長な同一 gateではない。** 下流ガードは raw record 導出時に初めて呼ばれます（[p3_b4_raw_record_producer.py:1862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_raw_record_producer.py:1862)）。今回の gate は proposal load 時点です（[p3_s4_loop.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:479)）。新負例も raw producerを呼ばず loaderだけで停止します（[test_p3_b4_proposal_binding.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:134)）。したがって `DW-M03` により M1–M3 を単独証拠から外す必要はありません。

  放置影響: bootstrap gateを外すと campaign実行後にだけ raw producerが拒否し、「走ったがreportに現れない」経路が再開します。

## 過剰拒否の検査

- **refuted — 正当な formal bootstrap の過剰拒否はない。** manifest は registry の適格行から先頭201件を生成し（[p3_b4_analysis_ledgers.py:1071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:1071)）、loader は同じ registry/seed から完全再生成して一致を要求します（[p3_b4_prerun_issuer.py:1140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:1140)）。したがって manifest 内 ID は一意です。201件より後の registry 行を拒否するのは D1880 の意図した縮小です。

  放置影響: manifest内 formal bootstrap の受理集合・参照 hash は維持されます。

- **refuted — 既存 fixture の想定外赤化経路なし。** 共通 fixture はちょうど201件を発行し、選択する attempt は先頭行です（[p3_b4_proposal_binding_support.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/p3_b4_proposal_binding_support.py:61)）。既存 base/sort/trigger 統合 fixtureも同じ helperを使用します（[test_p3_s4_loop.py:4416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_s4_loop.py:4416)）。

  放置影響: 既存正例の受理、WAL、report、参照値に静的な変化はありません。

- **real・nit — 新負例は strict publication の実在経路を通していない。** registry rowを `replace()` で後付けし、issuer loaderを monkeypatchしています（[test_p3_b4_proposal_binding.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:107)、[同:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:126)）。追加 row は元 row の `block_id`・ordinalも複製するため、そのままでは正規 loaderが受理する publicationではありません。一方、201件超の正規 registryからmanifest外行が生じること自体は既存 test が別途証明しています（[test_p3_b4_analysis_ledgers.py:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_analysis_ledgers.py:416)）。

  放置影響: M1–M3 は引き続き killできますが、strict issuer→loader→bootstrap の一本化された回帰証拠にはなりません。production受理集合は変わらないため must-fix にはしません。

## must-fix 一覧

1. **焦点走へ `test_p3_b4_admission_record.py` を追加。**
2. **焦点走へ `test_p3_b4_producer_auth_experiment.py` を追加。**
3. **collection meta-testとして `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` を追加。**

production実装そのものの must-fix はありません。

## 総括

D1880 の gate は3 driverの bootstrapだけに作用し、continuation・既存正例・正当な manifest 内入力を過剰拒否していません。下流 `_manifest_row()` とも到達時点が異なるため、M1–M3の単独証拠を `DW-M03` で外す理由はありません。

主な問題は焦点走の consumer 漏れ2 fileと collection meta-test 1件です。台帳への新 node登録は不要です。検査は静的のみで、追加焦点走を含む green は確認していません。