全体判定: **NO-GO**

### B-01 / `_perf_for` 単独変異は Layer-3 から不可視

- 根拠: [p3_autonomous_workload_trial.py:734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:734) は `PerfConfig(records=records, threads=threads, ...)` を実測 driver へ渡す一方、cell に残すのは [同:3003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:3003) の `"workload_flags": dict(entry["ycsb"])` だけである。Layer-3 は [autonomous_trial_completeness.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:546) の `descriptor.scale` と [同:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:583) の campaign `search_config` を entry と比較するだけで、実際に消費された `PerfConfig` を読まない。`_prepare_manifest_campaign_identity` も [producer:1055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:1055) から campaign を作るだけで `_perf_for` を呼ばない。
- 深刻度: **must-fix**
- 成果物影響: `_perf_for` を 100,000 records / 4 threads へ戻しても descriptor と campaign は 1,000,000 / 48 のまま Layer-3 を通り、レポートが実測 benchmark の scale を誤表示して比較対象を取り違える。

### B-02 / enlarged `WORKLOADS` が未承認の formal Layer-3 受理枝を暗黙に作る

- 根拠: [producer:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:226) で rr80/rr20 を `WORKLOADS` へ追加した結果、Layer-3 の [consumer:2962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:2962) は `workload not in producer.WORKLOADS` だけで formal workload を通す。一方、同じ検査は [consumer:588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:588) で `"pilot_scope": "exploratory-ycsb-abc"`、[consumer:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:131) で `"T-178 exploratory YCSB A/B/C ... no formal descriptor claim."` を要求する。`assert_campaign_layer3_chain` の入力には [consumer:2915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:2915) のとおり profile selector が無い。
- 深刻度: **must-fix**
- 成果物影響: rr80/rr20 の一貫した artifact が exploratory identity のまま Layer-3 accepted report になり、裁定 2.7 が実装しないとした formal Layer-3 受理集合と参照を暗黙に追加する。

### B-03 / M7 の新テストは旧 descriptor digest gate に mask される

- 根拠: [test_autonomous_trial_completeness.py:2986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_autonomous_trial_completeness.py:2986) は descriptor scale と `descriptor_binding.output_sha256` だけを変え、campaign.lock の `search_config.descriptor_sha256` を再構築しない。M7 の新検査を削除しても [consumer:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:583) から [同:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:601) の既存比較が同じ入力を `"search_config.descriptor_sha256 differs"` で拒否する。新テストが赤になるのは [test:2992](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_autonomous_trial_completeness.py:2992) の診断文が変わるためだけである。
- 深刻度: **must-fix**
- 成果物影響: M7 が偽 KILLED と台帳へ記録され、descriptor と campaign を自己整合させた変異に対する独立再投影の検出力が未証明のまま受入済みになる。

### B-04 / M8〜M11 は削除対象が冗長 gate または診断順序であり帰属しない

- 根拠: M8 の module/producer 比較 [producer:790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:790) は legacy/producer 比較 [同:836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:836) と consumer 三者比較 [consumer:2767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:2767) に mask される。M9 の `producer_digest != arm_digest` は同じ if 内の `producer_bytes != arm_bytes` [producer:807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:807) に論理的に包含される。M10 のテストは [test:3028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_autonomous_trial_completeness.py:3028) の loader 呼出回数を pin するが、弱い comparator が受理する同時改変正例を持たない。M11 を削除しても admission は [trial_registry.py:1390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/trial_registry.py:1390) の `u4-holdout-workload` で同じ入力を拒否し、新テスト [test_p3_autonomous_workload_trial.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_p3_autonomous_workload_trial.py:528) が pin するのは拒否順序だけである。
- 深刻度: **must-fix**
- 成果物影響: M8〜M11 の kill が実効受理集合の変化ではなく冗長比較や診断文へ帰属し、変異台帳が formal source と fail-closed の保証を過大表示する。

### B-05 / structured entry の consumer 取り残しで既存6 nodeが静的に赤

- 根拠:
  - [test_p3_autonomous_workload_trial.py:5747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_p3_autonomous_workload_trial.py:5747): `search_config["ycsb"] == A.WORKLOADS["rr80"]`
  - [同:5818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_p3_autonomous_workload_trial.py:5818): `cell["workload_flags"] == A.WORKLOADS["rr80"]`
  - [同:6121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_p3_autonomous_workload_trial.py:6121) と [同:6154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_p3_autonomous_workload_trial.py:6154): `"rr80" not in A.WORKLOADS`
  - 実装子未列挙の追加赤: [test_campaign.py:9227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_campaign.py:9227) は `workloads=list(autonomous.WORKLOADS)` を exploratory admission へ渡すため、新しい rr80/rr20 が [trial_registry.py:1390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/trial_registry.py:1390) で拒否される。
  - [test_s8c_preregistration_predicates.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_s8c_preregistration_predicates.py:151) は C01 を `workload-projection-mismatch` に固定するが、新しい3 sink は 1,000,000/48 literal を持つため [s8c_preregistration_evidence.py:1423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/s8c_preregistration_evidence.py:1423) を通過し、`load_ratified_freeze` 不在により [同:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/s8c_preregistration_evidence.py:1440) の `ratified-generation-reference-absent` へ変わる。
- 深刻度: **must-fix**
- 成果物影響: 既存受入 suite が6 node赤となり、formal entry の射影形と C01 gap reason を束縛する台帳参照を確定できない。
- 実装子報告との差分: 報告済み5 nodeに、`test_campaign.py::test_autonomous_trial_env_run_root_and_worktree_container_gate` が1件追加。

### 変異 M1〜M12 の帰属判定

| 変異 | 判定 | 理由 |
|---|---|---|
| M1 | 登録せず再照準 | flat entry は多数の caller で `entry["records"]` 等の `KeyError` を起こし、entry schema test 単独ではない。 |
| M2 | 登録せず再照準 | synthetic 3-sink、manifest identity、既存 campaign-id binding が同時に赤になりうる。 |
| M3 | 登録せず実効 gate を先に追加 | direct sink test は殺せるが、実 artifact の Layer-3 は `_perf_for` scale を観測しない。B-01。 |
| M4 | 登録せず再照準 | formal 経路は `_assert_formal_entry_binding` が Layer-3 より前に拒否し、複数テストも同時に赤になる。探索用の単一 fixture へ分離すべき。 |
| M5 | 登録可能 | exploratory cell に限定すれば `cells[].workload_flags differs from producer` が単一理由になる。 |
| M6 | 登録可能 | formal descriptor が entry と一致する fixtureなら、campaign `records/threads` 比較だけへ帰属できる。 |
| M7 | 登録せず再照準 | campaign.lock まで変異後 descriptor に合わせない限り既存 digest gate に mask される。B-03。 |
| M8 | 登録せず再照準 | producer、legacy、module、consumer の比較が重複し、一箇所削除は他層に mask される。 |
| M9 | 登録しない | digest 同値比較は同じ if の canonical bytes 同値比較に包含されるため等価変異。 |
| M10 | 登録せず再照準 | loader call-count は診断 pin。弱い三箇所自己一致が通す同時改変正例が必要。 |
| M11 | 登録せず両層変異へ再照準 | formal fail-closed 単独削除は `u4-holdout-workload` に mask される。 |
| M12 | expected node 修正後に登録可能 | producer 単体 test に加え、`test_wave_files_do_not_contaminate_production_holdout_scan` も同じ source hit を検出する。records/threads だけの負対照も未登録。 |

### 非回帰と網羅の確認

- read-only import probeでは canonical SHA-256 は ycsb-a `8e7d4c37…`, ycsb-b `c749c201…`, ycsb-c `36be6867…` と baseline に一致した。campaign ID も既存 goldenの `4b75e24e`, `136086b0`, `4ac6e6a4` に一致した。pytest は実走していない。
- p3 module importer を先に全列挙してから各 alias を検査した。`WORKLOADS` を実際に読むのは productionでは `autonomous_trial_completeness.py`、testsでは `test_p3_autonomous_workload_trial.py`, `test_campaign.py`, `test_autonomous_trial_completeness.py`, `test_layer3_report.py`, `test_reflux_originless_compatibility.py`。取り残しはB-05の5箇所。
- 新規 test fileや改名は無い。追加12 nodeは既存2 file内だけで、file集合 meta-testと逐語 node台帳の追加波及は静的には見つからなかった。

## 総括

最大の穴は、実測に使う `_perf_for` scale が artifactへ束縛されず、Layer-3が誤った実測scaleを受理できる点である。  
加えて、formal profileを追加しただけで exploratory Layer-3の受理集合がrr80/rr20へ広がっている。  
M7〜M11は既存gateによるmaskまたは診断差をkillと数える形で、変異帰属も成立していない。  
既存6 nodeの静的赤を含め、このsnapshotはland不可である。