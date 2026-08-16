## 1. 8c launch の実行文脈

静的に追跡した実測経路は次のとおりである。

```text
p3_autonomous_workload_trial.main
  :3286-3307
-> run_trial
  :2726-3075
-> _finish_trial
  :1928-2259
-> _run_workload
  :2279-2688
-> trigger._admit_env_contract
  :2342
-> _prepare_campaign_identity
  :2348-2355
   -> _campaign_for
      :635-672
   -> _perf_for
      :675-682
-> _drive_s8c_generation
  :2635-2651
-> p3_s4_loop_trigger_gating.drive_iteration
  :718-830
-> _run_one_iteration_resolved
  :549-610
-> loop.run_campaign
  :595-604
-> p3_s4_loop.run_campaign
  :92-270
-> pipeline.evaluate
  :256-265
-> pipeline._run_bench
  :405-471
-> calibrator.measure_point
  :451-465
-> subprocess_runner
  :440-441
```

実行文脈の判定は以下である。

- `_campaign_for` は `CampaignConfig` を組み立て、実際に解決された環境契約を `bound_environment_contract` へ束縛する。`orchestrator/campaign/p3_autonomous_workload_trial.py:635-672`
- `_perf_for` は 100,000 records、4 threads、execution time 1、2 repetitions を設定する。`同:675-682`
- `_run_workload` は `trigger._current_site()` と `trigger._admit_env_contract(resolved_site)` を実行してから campaign identity と perf を作る。`同:2335-2386`
- 標準 drive は dispatch しない。最終的には同じノード上で `subprocess_runner` がベンチコマンドを直接起動する。`orchestrator/campaign/calibrator.py:397-441`
- Pegasus login で `do_build=True` は `_assert_build_site_opted_in` により、artifact や provider の生成前に拒否される。`p3_autonomous_workload_trial.py:1659-1674,2871-2878`
- pipeline にも login/suspect site の実測拒否がある。`orchestrator/campaign/pipeline.py:405-422`
- ただし `do_build=False` の `run_trial` 自体は login でも開始できる。run root、journal、部分 report を作ってから後段で止まりうる。従って「`run_trial` は常に計算ノード上」とは言えない。
- `OTHER` site は build を許可され、linux-baremetal 契約で実測可能である。`p3_autonomous_workload_trial.py:1665-1667`、`env_contract.py:283-303`
- site 判定は hostname 由来で、PBS 環境変数を参照しない。`orchestrator/campaign/site_policy.py:30-45,66-84`
- compute transport admission が確認するのは主に `PBS_JOBID` と proxy 条件であり、`IZANAGI_RESERVATION_*` 一式ではない。`orchestrator/campaign/claude_provider.py:180-198,342-357`
- `run_trial` から `reservation.read_binding`、`check_reservation`、tracked `reservation.json` のいずれにも到達しない。
- tracked positive control は `output/env/pegasus/calibration/job-staging/0:867876.nqsv/reservation.json:1-10` にあるが、8c launcher はこれを読まない。

結論として、8c は自動 dispatch 経路ではなく「呼び出されたノードで実測する」経路である。実測は Pegasus login では拒否されるが、PBS のない `OTHER` site では起動可能である。また compute でも tracked `reservation.json` と `IZANAGI_RESERVATION_*` が存在する保証はない。従って無条件の reservation 読み出しは、正当な `OTHER` 実測を fail-closed で壊す。

## 2. isolation policy との接続

親 brief の P4 は、関数名を除けば成立する。

- 実型 `IsolationPolicy` は `single_process` と `allow_resume` を持つ。`orchestrator/campaign/env_contract.py:56-69`
- `ExecutionEnvironmentContract.isolation_policy` が実 field として存在する。`同:92-111`
- Pegasus 契約は `single_process=True, allow_resume=False`。`同:248-260`
- linux-baremetal、すなわち `OTHER` は `single_process=False, allow_resume=True`。`同:283-303`
- `_run_workload` は実際の site からこの契約を解決する。`p3_autonomous_workload_trial.py:2335-2342`
- `_campaign_for` は同じ契約を downstream の `CampaignConfig.bound_environment_contract` に格納する。`同:635-672`、`orchestrator/campaign/model.py:67-84`
- `reservation.is_reservation_required` はこの型を直接受け取る。`orchestrator/campaign/reservation.py:273-277`

従って新しい CLI、search config、trial config の新設は不要である。接続位置は、契約が確定する `_run_workload:2342` の直後でよい。

ただし C12 が要求する正確な名前は `reservation.single_process_required` であり、現実装は `is_reservation_required` である。この小さな API 差は閉じる必要がある。また run 全体を workload より前に admission したい場合は、site、環境契約、reservation check を保持する新しい run-scope 型と引き回しが必要になり、変更範囲は `_finish_trial`、`_run_workload`、report schema、テスト fixture まで広がる。今回の最小案ではその設定面を新設せず、解決済み契約の位置で admission する。

## 3. 両案の実装形

以下の「赤」は静的予測である。pytest は実行していない。

### 採用案: isolation policy による条件付き配線

#### 実装面

1. `orchestrator/campaign/reservation.py:273-277`

   `single_process_required(isolation_policy)` を正本の `def` として追加し、現在の型検査と `single_process` 判定を移す。既存 consumer を壊さないよう、`is_reservation_required` は新関数へ委譲する互換 wrapper とする。

   単なる代入 alias では C12 の AST が FunctionDef を発見できないため不可である。`orchestrator/campaign/s8c_preregistration_evidence.py:288-298,599-605`

2. `orchestrator/campaign/p3_autonomous_workload_trial.py:39-47,102`

   `reservation` を import する。

3. `同:2279-2355`

   `_run_workload` が実 site と契約を解決した直後、identity、layout、role、drive より前に次を行う。

   - `reservation.single_process_required(contract.isolation_policy)` を呼ぶ。
   - false、すなわち `OTHER` の場合は PBS や reservation 環境を読まず通過する。
   - true の場合のみ `reservation.read_binding(os.environ)` と `reservation.check_reservation(...)` を呼ぶ。
   - failure は campaign identity、artifact layout、ベンチ subprocess より前に発生させる。

   `read_binding` の入力と検証項目は `reservation.py:120-129,159-175,218-270` にある。

4. `p3_autonomous_workload_trial.py:2635-2651`

   required site では drive の直前にも `ReservationCheck.recheck` または `ensure_remaining` を行い、role 実行中に期限を使い切った reservation でベンチを開始しない。

5. `同:2373-2383,2188-2221`

   成功した check から allocation receipt を生成し、cell と最終 report に格納する。最低限含める値は次である。

   - environment contract SHA
   - `single_process` と `allow_resume`
   - PBS job ID、hostname、boot ID
   - script digest、nonce
   - required seconds、safety margin、残存秒
   - check 実行時刻

   `run_trial` は既に既存 run root の再利用を拒否する。`同:2879-2884`  
   trigger にも resume policy の検査がある。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:350-367,770`

6. `orchestrator/campaign/autonomous_trial_completeness.py:1311-1355,2000-2060`

   完了 artifact が allocation receipt を主張するなら、存在、型、契約との一致、cell 間の一致を completeness 側でも検証する。ここを触らなければ runtime rejection は閉じるが、「保存された receipt を consumer が検証する」という乖離は残る。

   schema v4 への bump は避け、v3 の追加 field とする。bump すると既存 schema test と fixture の変更量が不必要に増える。

#### 既存 nodeid への影響

推奨位置へ gate を入れると、現在 reservation admission を用意せず compute drive 到達を期待する次の既存テストが赤になる。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_pegasus_workload_identity_layout_and_drive_use_pegasus_contract`

completeness で build receipt を必須化する場合、次の fixture も allocation receipt を補わない限り赤になる。

- `orchestrator/tests/test_autonomous_trial_completeness.py::test_build_file_verification_with_cells_still_requires_campaign_root`

schema を v4 に上げる案を選ぶ場合は、少なくとも以下も赤になるため、推奨しない。

- `orchestrator/tests/test_autonomous_trial_completeness.py::test_role_schema_v3_and_report_schema_v3_are_required`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_fixture_trial_runs_ycsb_abc_and_binds_descriptor`

次は維持すべき既存 positive/negative controls である。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_other_workload_identity_layout_and_drive_use_linux_contract`
- `orchestrator/tests/test_reservation.py::test_recorded_pegasus_reservation_passes_live_admission`
- `orchestrator/tests/test_reservation.py::test_required_is_derived_from_typed_isolation_policy`
- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_lookup_error_propagates_before_campaign_and_wal`
- `orchestrator/tests/test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink`

追加すべき受入 nodeid は次の形にする。

- `test_required_pegasus_reservation_precedes_8c_campaign_launch`
- `test_missing_or_mismatched_pegasus_reservation_never_reaches_drive`
- `test_other_measurement_does_not_read_reservation_environment`
- `test_recorded_pegasus_reservation_reaches_8c_gate`
- `test_allocation_receipt_is_required_and_tamper_evident_for_single_process_contract`

recorded positive は tracked JSON の literal を独立に固定し、時刻と boot ID だけを注入する。expected 値を production loader から取得してはならない。

#### 閉じるもの、残るもの

閉じるもの:

- Pegasus single-process 契約から reservation admission までの実 runtime 経路
- exact symbol `reservation.single_process_required`
- job、host、boot、script、nonce、期限、容量の fail-closed 検査
- resume 禁止と allocation receipt の永続化

残るもの:

- C12 の module-local AST が cross-module の lookup と attestation を見失う問題
- C12 が `machine_checkable=false` であるため evaluator が実行されない問題
- `check_reservation` は reservation binding の整合性を検証するが、OS 上で他プロセスが絶対に存在しないこと自体は証明しない
- 8c を投入する wrapper が `IZANAGI_RESERVATION_*` を供給する operational wiring は別途必要である。未配線の compute 実行は意図どおり拒否される

### 非採用案: C12 から allocation reservation を de-scope

#### 本 wave で実装可能な形

所有競合を避けると、この wave でできるのは裁定と handoff の記録だけである。

- `docs/spool/decisions/<new-fragment>.md:1` に de-scope 裁定、失う保証、T-1184 の必要変更を記録する。
- `docs/spool/worklog/<new-fragment>.md:1` に未解消の契約乖離と T-1184 への handoff を記録する。
- production code、契約 JSON、freeze record は変更しない。

失う保証は明記する。

- allocation、PBS job、boot ID、deadline の provenance を 8c acceptance 条件にしない
- reservation 欠落を 8c launch で機械的に拒否しない
- single-process と resume 禁止を allocation evidence として主張しない

これは本 wave で可能な記録形ではあるが、契約と実装の乖離そのものは閉じない。

#### T-1184 に委ねる実装形

T-1184 が所有する面で一貫した revision を作る。

- `docs/phase3-8c-preregistration.md:188-193`  
  Condition 12 を environment/calibration のみへ縮小し、allocation isolation は非保証と明記する。
- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:430-485`
  - `:434-446` の allocation receipt、single-process、resume fields を削除
  - `:449-460` の isolation allocation 要求を縮小
  - `:470-476` の `allocation_consumer` を削除
  - `:479-485` の proof、static note、negative control を書き換え
- `orchestrator/campaign/s8c_preregistration_evidence.py:578-610`  
  `_evaluate_c12` から reservation branch を除き、実際の cross-module route を表現できる述語へ改める。
- `orchestrator/tests/test_s8c_preregistration_predicates.py:399-418,473-497`  
  token-only fixture と C12 negative control を新しい保証に合わせる。
- `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g3.json:1`  
  g1/g2 を変更せず、新しい generation を追加する。

#### 既存 nodeid への影響

契約だけを変更し、successor freeze を追加しない状態では次が赤になる。

- `orchestrator/tests/test_s8c_preregistration_core.py::test_current_evidence_contract_hash_is_frozen`
- `orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`

C12 negative control の意味を変えるため、次の既存 parameter case は更新対象になる。

- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_noop_and_token_only_fixtures_never_satisfy[nc_c12_resume_or_multi_process_allowed-C12]`

次は変更せず緑を維持しなければならない。

- `orchestrator/tests/test_s8c_preregistration_core.py::test_existing_g1_record_pins_are_unchanged`

de-scope は文書上の過大な主張を閉じる一方、実測 artifact が予約外プロセスや誤った job 文脈から影響を受ける実欠陥を意図的に残す。

## 4. 親 brief P3 の検証

P3 の「A は実行されるが静的述語から見えない、B は実際に欠ける」という二分は、lookup の行位置に訂正が必要だが、結論として成立する。

実 route は次である。

- `_run_workload` が `trigger._admit_env_contract` を呼ぶ。`p3_autonomous_workload_trial.py:2335-2342`
- trigger の `_admit_env_contract` が module alias `_lookup=env_contract.lookup` を呼ぶ。`p3_s4_loop_trigger_gating.py:100-101,324-330`
- standard drive が `_run_one_iteration_resolved` から `loop.run_campaign` を呼ぶ。`同:549-604,718-830`
- `loop.run_campaign` が `_authorize_measurement` を呼ぶ。`orchestrator/campaign/p3_s4_loop.py:92-133`
- required attestation では `attest_and_build_receipt` が実行される。`同:61-89`、特に `:77-78`
- authorization 完了後に pipeline evaluation と実測へ進む。`同:256-265`

従って 8c の標準 production launch は本当に `loop.py` の sink を通る。

ただし親 brief の「lookup が `loop.py:68` で走る」は不正確である。`loop.py:68` は `execution_guard.require_certified_writer_authorization` であり、環境契約の lookup は upstream の `p3_s4_loop_trigger_gating.py:324-330` で実行される。

述語が見失う理由も確認できる。

- `_called_names` は与えられた module の call 名だけを収集する。`s8c_preregistration_evidence.py:288-298`
- `_reachable_functions` は同じ module の top-level FunctionDef だけを辿る。`同:341-351`
- C12 は p3 module の `run_trial` から得た reachable calls に lookup、attest、reservation 名をすべて要求する。`同:578-610`
- そのため trigger module にある lookup と loop module にある attestation は、実行されても p3 module-local AST から見えない。
- さらに現在の契約は C12 を `machine_checkable=false` としており、通常評価は `_evaluate_undefined` へ送る。`同:699-710`、契約 JSON `:430-485`

よって A は観測欠陥、B は runtime 欠陥である。配線後も A を別途修正しない限り、C12 の機械判定は EVIDENCE_UNDEFINED のままである。

## 5. 編集面の衝突

de-scope の完全実装は、稼働中の T-1184 が所有する bytes を必ず変更する。

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`
- `output/s8c-preregistration/condition-freeze/`

さらに normative source の C12 も改訂しなければ、JSON だけを縮小して文書と矛盾する。

従って T-1167 内では次の境界とする。

- 条件付き配線案は上記所有面を変更せず実装可能。
- de-scope 案は decision/worklog fragment による裁定記録と T-1184 handoff まで。
- 契約 JSON、C12 predicate、normative source、新 generation freeze は T-1184 側で同一変更として実装する。
- 既存 g1/g2 freeze は上書きしない。追加するなら g3 とする。

## 6. 凍結 pin 閉包

契約変更に影響する閉包は次のとおりである。

1. 契約の semantic pin

   - `evidence_contract_sha256`: `orchestrator/campaign/s8c_preregistration.py:374-382`
   - canonical JSON を hashing するため、意味内容を pin するが、空白や key 順を含む raw bytes の完全 pin ではない。

2. protected contract hash

   - `MarkdownContract.protected_sha256`: `同:183-191`
   - evidence semantic hash、normative body、section 5 の field names、section 6 の hashes を結合する。
   - freeze schema fields: `同:73-88,194-207`

3. generation ledger の列挙と検証

   - source、evidence contract、全 freeze generation の収集: `同:1377-1394`
   - evidence blob の git OID 取得: `同:1445`
   - semantic evidence hash と protected hash の再計算: `同:1449-1457`
   - generation transition 検証: `同:1466`
   - final evidence OID と candidate state: `同:1484-1493`

4. revision 作成側

   - worktree contract 読み出し: `同:1759-1763`
   - protected hash が同一の無意味な revision を拒否: `同:1765-1766`
   - record document の生成: `同:1685-1710`
   - successor を exclusive create: `同:1775-1783`

5. 実台帳

   - `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json:1`
   - `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g2.json:1`

   g1 と g2 は同じ evidence semantic hash を持つ一方、protected hash は normative source の revision により異なる。次回変更では双方を保持し、g3 を追加する。

6. test pin

   - current evidence hash の固定値:  
     `orchestrator/tests/test_s8c_preregistration_core.py:1123-1126`
   - g1 の不変 pin:  
     `同:1129-1137`
   - current candidate と generation chain の整合:  
     `orchestrator/tests/test_s8c_preregistration_invariant.py:125-160`

7. raw contract blob の証拠閉包

   - predicate evidence の `contract_ref` は raw blob SHA を持つ。`orchestrator/campaign/s8c_preregistration_evidence.py:687-700`
   - 各 condition probe がこの参照を evidence に含める。`同:394-408`
   - core/evaluator exact blob identity は `s8c_preregistration.py:1596-1599,1622-1632`
   - activation report 全体は `_activation_report_digest` で hash される。`同:1808-1812`

従って契約 JSON の意味変更は freeze semantic pin、protected hash、generation chain、current-hash test、predicate evidence、activation report digest まで波及する。空白だけの変更でも raw contract reference と report digest は変化しうる。

## 総括

採るべきは、解決済み `contract.isolation_policy` による条件付き配線である。  
Pegasus では fail-closed、`OTHER` では reservation 環境を要求しないため、実行文脈と一致する。  
P3 の A は実在する観測欠陥であり、lookup の実位置だけ親 brief から訂正が必要である。  
de-scope は T-1184 の所有 bytes を変更しなければ完結せず、本 wave 内では実装不能である。  
最大の未確定は reservation safety margin の定義と、check が実プロセス排他まで証明しない点である。