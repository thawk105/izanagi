## 0. 参照した現物

- 親 brief で、本 wave は実装を伴わない 5 点の前提設計であり、D201・D183・D114・D211、本番 authority 不変、発行 3 条件後の人間承認 provisioning が固定されていることを確認した。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-8c-wiring-design/brief.md:6-38`
- V-1〜V-5 の裁定は、V-2 が trusted physical harness、V-3 が同一 wire の R 回実行、V-4 が launch admission 発行 capability、V-5 が結線前の crash 設計である。fixture binding では production client の既定解決を拒否する要件も明記されている。`output/insights/2026-08-06_t244-p3-8c-wiring/s4-adjudication.md:141-169`
- U-10 は `imax=4 / qmax=68 / kmax=1 / Bmin=2 / candidate_min=1 / F=33 / R=1` を批准したが、V-2 の exact schema・issuer・consumer は設計 wave へ残し、topology 確定後に再計数し、異なれば再批准すると定める。`output/insights/2026-08-06_t244-u10-budget-values/README.md:220-247` `同:301-345` `同:368-391`
- 現 authority は 71 bytes、`origins=[]` の 1 行である。`orchestrator/campaign/reflux_origin_authority_v2.json:1`
- `derive_cell_key` は `workload.descriptor_sha256 / axis_semantics_sha256 / verifier_policy_sha256 / environment_contract_sha256` の順序付き 4 要素を domain-separated canonical JSON として SHA-256 する。`orchestrator/campaign/reflux_origin_ledger.py:485-493`
- ledger は同一 authority blob 内の同一 4-tuple を拒否するが、参照 artifact の中身は dereference しない。`orchestrator/campaign/reflux_origin_ledger.py:1824-1865` `同:205-209`
- `OpenedBatchMember` と `SealedBatchMember` の実 field、および 6 event、`OriginSnapshot`、`EventReceipt.replayed` を確認した。`orchestrator/campaign/reflux_origin_ledger.py:496-629`
- outcome 受理集合は `accepted / rejected / tombstoned` の 3 値で、前二者は evidence 必須、`rejected` は constraint 必須、tombstone は両方禁止である。`orchestrator/campaign/reflux_origin_ledger.py:682-726`
- seal 時には wire 正準性、origin-canonical `replicate_ordinal`、commitment opening、tombstone の終端 suffix が検査される。`orchestrator/campaign/reflux_origin_ledger.py:1457-1596`
- `TrialBinding`、`TrialLaunchAdmission`、seal 検査、fresh re-derivation、JSON record は実在するが、origin・cell・descriptor digest は admission field にない。`orchestrator/campaign/trial_registry.py:124-149` `同:1251-1357`
- 8c は descriptor と campaign identity を事前導出し、report の `cells[i]` に `descriptor / descriptor_binding / campaign_id / campaign_root` を残すが、現 admission では `campaign_id` のみを照合して元 admission を返す。`orchestrator/campaign/p3_autonomous_workload_trial.py:549-682` `同:1652-1680`
- 現 8c は generation ごとに `drive()` を 1 回呼び、その戻り値には最低限 `outcome / variant / stop_reason / iteration / ran` しか要求しない。per-query evidence 正本ではない。`orchestrator/campaign/p3_autonomous_workload_trial.py:1688-1913`
- 正準 mask 集合は `mask=0..31` の 32 点であり、wire は 5 文字 LSB-first である。`orchestrator/campaign/trigger_gate_binding.py:78-108` `orchestrator/campaign/reflux_ir.py:113-141`
- workload descriptor の digest は canonical JSON bytes の SHA-256 で、report の `descriptor_binding.output_sha256` に現れる。`orchestrator/campaign/s8b_descriptor.py:36-43` `同:194-205`
- environment contract は全 field の canonical JSON digestを `contract_sha256` とし、実行 provenance に `contract_sha256 / execution_receipt_sha256 / execution_receipt` が現れる。`orchestrator/campaign/env_contract.py:83-160` `orchestrator/campaign/p3_s4_loop_trigger_gating.py:357-370`
- P6 は last-wins の `records_by_stage()` を禁止し、順序付き WAL、source 観測前の hypothesis/validation commit、4 値の formal result を要求する。`output/insights/2026-08-03_t244-p6-contract/README.md:116-180` `同:209-280`
- 読み取りは静的な現物確認のみである。ファイル変更・commit・pytest・probe・物理実行はすべて未実走である。

## 1. source closure

### (a) 現状の現物

4 referent の現状は次のとおりである。

| manifest field | digest 対象となる bytes | 実成果物での照合点 | 現在の閉包 |
|---|---|---|---|
| `workload.descriptor_sha256` | `s8b_descriptor._canonical_bytes(descriptor)`。sort key、compact separator、UTF-8、末尾 LF なし。`orchestrator/campaign/s8b_descriptor.py:36-43` | `report.cells[i].descriptor` を同じ規則で再直列化し、`report.cells[i].descriptor_binding.output_sha256` と比較する。scale は authority の `workload.records / threads` と `descriptor.scale` を比較する。`orchestrator/campaign/p3_autonomous_workload_trial.py:1652-1677` `orchestrator/campaign/s8b_descriptor.py:121-132` | producer と runtime field は実在する。 |
| `axis_semantics_sha256` | D179 に従えば、捕捉 commit `H` にある人間承認済み・名前付き axis-semantics artifact の raw Git blob bytes。コード定数や emitter の再実行結果は trust root にしない。`docs/decisions.md:8807-8810` | runtime は provenance の `axis / pin / gate_record` と、各 WAL の `TriggerGateBinding.mask / predicate_sha256 / source` で照合する。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:264-293` `orchestrator/campaign/trigger_gate_binding.py:136-202` | 現 repo には「この名前付き blob を preimage とする」という批准済み規則がない。D163 も未解決と記録する。`docs/decisions.md:8106-8110` |
| `verifier_policy_sha256` | `legacy+s2` の pass 集合、全 pass 必須、accepted/rejected/tombstone 対応、witness 正規化を列挙した名前付き verifier-policy artifact の raw Git blob bytes。`docs/decisions.md:8807-8810` | prospective config は `search_config["verify"]="legacy+s2"`、成功側は terminal `commit.payload.verify_configs`、失敗側は順序付き WAL の terminal `abort` と照合する。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:449-469` `orchestrator/campaign/pipeline.py:1003-1034` | policy 値と WAL field は実在するが、digest の正本 artifact は存在しない。`docs/decisions.md:8106-8110` |
| `environment_contract_sha256` | `ExecutionEnvironmentContract._canonical_obj()` の canonical JSON UTF-8 bytes、末尾 LF なし。`orchestrator/campaign/env_contract.py:145-160` | digest を `resolve_by_contract_sha256` で一意解決し、物理実行 provenance の `contract_sha256` と比較する。`orchestrator/campaign/env_contract.py:355-380` `orchestrator/campaign/p3_s4_loop_trigger_gating.py:357-370` | producer と runtime field は実在する。名前付き projection blob は provisioning 材料として必要。 |

bare な `descriptor_sha256` という名前は使わない。以後は必ず、manifest の `workload.descriptor_sha256`、report の `cells[i].descriptor_binding.output_sha256`、campaign config の `search_config["descriptor_sha256"]` を分けて表記する。後二者は実際に別 field path である。`orchestrator/campaign/reflux_origin_ledger.py:395-429` `orchestrator/campaign/p3_autonomous_workload_trial.py:549-565`

### (b) 設計

docs では、authority provisioning の入力となる create-once の `source-closure/v1` record を次の exact key 集合で定義する。

- `schema_version`
- `captured_commit_oid`
- `authority_series_id`
- `origin_id`
- `cell_key`
- `referents`

`referents` の key は裸の識別子でなく、exact に次の 4 個だけとする。

- `workload.descriptor_sha256`
- `axis_semantics_sha256`
- `verifier_policy_sha256`
- `environment_contract_sha256`

各値は `preimage_ref={path,sha256}`、`digest_rule`、`producer_field`、`runtime_field_paths` を持つ。`path` は `captured_commit_oid:path` で読む Git blob を指し、`sha256` は live file や再直列化結果でなく、その raw blob bytes の digest とする。workload と environment の projection artifact は、それぞれ既存 canonical bytes と raw blob bytes が完全一致する形、すなわち末尾 LF なしに限定する。既存正準化規則は `s8b_descriptor.py:36-43` と `env_contract.py:145-160` にある。

発行時検査は次の順序に固定する。

1. `captured_commit_oid` を full commit として 1 回だけ解決し、その commit が新規 authority entry をまだ含まないことを検査する。これは authority 自身を source に含める自己参照を禁じる D179 の条件である。`docs/decisions.md:8807-8810`
2. 4 個の `preimage_ref.path` を `H:path` の Git blob として読み、raw bytes の digest を record と manifest の双方へ比較する。working-tree bytes は読まない。authority loader が現在行うのは hash 形式と導出 identity の検査だけなので、この検査を loader 済みとみなしてはならない。`orchestrator/campaign/reflux_origin_ledger.py:1824-1892`
3. workload projection を strict parseし、canonical 再直列化 bytes が元 blob と一致し、`cells[i].descriptor`、`cells[i].descriptor_binding.output_sha256`、authority の `records / threads` と一致することを要求する。`orchestrator/campaign/p3_autonomous_workload_trial.py:1652-1677`
4. axis artifact は marker、5 reason の順序、5-bit LSB-first wire、mask `0..31`、`kUnset` を閉じた schema で持つ。live conformance は `axis_trigger_gating`、`reflux_ir`、全 32 predicate と比較するが、それらのコード bytes 自体は trust root にしない。`orchestrator/campaign/reflux_ir.py:34-58` `同:113-141` `orchestrator/campaign/trigger_gate_binding.py:98-108`
5. verifier artifact は `legacy → s2` の ordered pass、accepted 条件、candidate-attributable rejected 条件、fail-closed 条件、単一 witness-class 制約を持つ。実走時には `commit.payload.verify_configs` または terminal `abort` の ordered WAL と比較する。`orchestrator/campaign/pipeline.py:1003-1034` `output/insights/2026-08-03_t244-p6-contract/README.md:138-180`
6. environment projectionを `resolve_by_contract_sha256` で一意解決し、物理実行時には provenance の `contract_sha256` と execution receipt を照合する。`orchestrator/campaign/env_contract.py:355-380`
7. 4 digest から `derive_cell_key` を再計算し、closure record、authority entry、launch capability の `cell_key` が一致しなければ発行しない。`orchestrator/campaign/reflux_origin_ledger.py:485-493`
8. provisioning commit には、候補 authority bytes の SHA-256、`origin_id`、`cell_key`、closure record の SHA-256 を束縛する人間承認 receipt を置く。これは one-origin の provisioning receipt であり、過去全世代を列挙する ever-issued 台帳ではない。
9. 実行時には capability と result-evidence record が同じ closure digest を保持し、formal consumer が prospective identity と実成果物の双方を再照合する。

重複防止の名乗りは「同一 authority blob 内」に限定する。現 loader が保証するのはその範囲だけであり、series の世代連続性や ever-issued 性は実装に存在しない。`orchestrator/campaign/reflux_origin_ledger.py:1836-1865` `docs/decisions.md:10019-10036`

### (c) 設計が依存する未確認の前提

- axis-semantics と verifier-policy の人間承認済み名前付き artifact は未存在である。これらが無い限り source closure は fail-closed し、authority provisioning へ進めない。`docs/decisions.md:8106-8110`
- provisioning receipt を authority blob と closure record へ束縛して launch admission が取得する経路も未存在である。
- environment の expected digest は launch 時点で capability に束縛できるが、actual digest は物理 site で `_admit_env_contract` が解決した後にしか確定しない。したがって capability は expected 値を持ち、reserve 前と evidence 発行時の二段階で actual 値を検査する必要がある。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:318-334` `同:621-638`
- SHA-256 の衝突困難性と、人間承認された commit の保持を前提とする。repo 内の履歴を append-only とみなす保証はしない。`docs/decisions.md:8784-8788`

### (d) 採らなかった案と理由

- live Python source、runtime 定数、emitter 出力を直接 hash する案は、import closure と自己参照を閉じないため採らない。`docs/decisions.md:8807-8810`
- manifest に書かれた 64 hex を再計算せず信用する案は、現在の authority loader と同じ穴を残す。`orchestrator/campaign/reflux_origin_ledger.py:395-441`
- `stock_certification_ref` や `role_bundle_sha256` を closure record の代用にする案は、別の semantic field を流用して同名異義を生むため採らない。
- repo 内で series 横断・全世代の重複を調べる案は D211 と矛盾する。`docs/decisions.md:9997-10036`
- axis/verifier artifact が欠けた場合に固定 hash、空 object、恒真な「現実装と一致」を置く案は、正本不在を緑へ変えるため採らない。

## 2. V-2 の exact 化

### (a) 現状の現物

ledger の `EvidenceDigest` は「claimed content digest」であり、ledger 自身は dereference しない。従って SHA の形が正しいだけの偽 evidence でも ledger の構造検査は通りうる。`orchestrator/campaign/reflux_origin_ledger.py:205-209`

現 driver は成功を `"certified"`、その他を広い `"aborted"` へ潰し、`records_by_stage()` の last-wins 射影を返す。legacy/S2 の複数 `verify_done` や attempt 区間を完全には保存しない。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:582-608` `orchestrator/campaign/wal.py:1406-1427`

P6 が読む構造化 anomaly は terminal abort の `payload.verify.anomalies` であり、`verify_done.payload.anomalies` は個数である。この二つを裸の `anomalies` として扱ってはならない。`output/insights/2026-08-03_t244-p6-contract/README.md:138-156`

### (b) 設計

#### result-evidence record

新規 `result-evidence/v1` record の top-level exact key は次の 9 個とする。これは設計上の新 schema であり、現実装に既存すると主張しない。

- `schema_version`
- `issuer`
- `origin_binding`
- `trial_binding`
- `ledger_member`
- `p6_plan`
- `trigger_binding`
- `physical_result`
- `evidence`

各 nested object は次で閉じる。

| object | exact field |
|---|---|
| `issuer` | `kind`。値は固定の trusted physical harness issuer ID。これは表示用であり、権限の根拠は launch capability と専用書込経路である。 |
| `origin_binding` | `authority_blob_sha256 / source_closure_sha256 / origin_id / cell_key / workload / axis_semantics_sha256 / verifier_policy_sha256 / environment_contract_sha256`。`workload` は authority と同じ `descriptor_sha256 / records / threads`。`orchestrator/campaign/reflux_origin_ledger.py:238-263` |
| `trial_binding` | `launch_admission_record_sha256 / campaign_id / workload`。元 record は `launch_admission_record()` の exact projectionである。`orchestrator/campaign/trial_registry.py:1295-1321` |
| `ledger_member` | `batch_id / iteration_index / query_ordinal / replicate_ordinal`。前二者は batch identity、後二者は member identity。`orchestrator/campaign/reflux_origin_ledger.py:533-562` |
| `p6_plan` | `purpose / hypothesis_sha256 / validation_plan_sha256`。`purpose` は `source` または `p6-validation` のみ。hypothesis と validation は source 観測前に固定する。`output/insights/2026-08-03_t244-p6-contract/README.md:211-223` |
| `trigger_binding` | `mask / candidate_wire / trigger_gate_binding_commitment`。wire は `encode_wire(TriggerGateIR(mask))` と byte-for-byte 一致させる。`orchestrator/campaign/reflux_ir.py:113-128` |
| `physical_result` | `build_attempt_id / outcome / constraint_sha256`。`outcome` は record 内では `accepted / rejected` のみ。tombstone record は発行しない。 |
| `evidence` | `ordered_wal_ref / execution_provenance_ref`。両方とも exact `{path,sha256}`。ordered WAL ref は last-wins dict でなく、当該 attempt の順序付き record 列を凍結した create-only projection を指す。`orchestrator/campaign/wal.py:1406-1427` |

record bytes は sort-key・compact separator の canonical UTF-8 JSON、末尾 LF なしとし、`EvidenceDigest.sha256` はその raw bytes 全体の SHA-256 とする。record 自身に自己 digest は含めない。

#### issuer、時点、置き場、create-only

issuer は、`run_campaign()` の terminal WAL と execution receipt を所有し、`contract / binding / summary / layout` が同時に存在する trusted physical harness の最終化点である。現物上は `_run_one_iteration_resolved()` の `run_campaign()` 後、outer outcome へ変換する前に相当する。outer 8c、planner/coder/auditor、report builder は issuer ではない。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:519-608`

書込み先は、実 report に残る `cells[i].campaign_root` を根とする deterministic path:

`<campaign_root>/reports/reflux-result-evidence/<origin_id>/<batch_id>/<query_ordinal>.json`

とする。`campaign_root` は現 report field である。`orchestrator/campaign/p3_autonomous_workload_trial.py:1670-1677`

順序は次に固定する。

1. ordered WAL projection と execution provenance projection を create-only で書き、file と parent directory を fsync する。
2. read-back と digest を確認する。
3. result-evidence record を create-only で書き、fsync・read-backする。
4. その後にだけ次の physical query へ進む。

強制手段は、root confinement と symlink ancestor 検査、`O_CREAT|O_EXCL|O_NOFOLLOW`、file fsync、parent fsync、read-back 完全一致である。既存 ledger writer と `_write_bytes_bound` がこの型を実在させている。`orchestrator/campaign/reflux_origin_ledger.py:2881-2914` `orchestrator/campaign/s8b_prediction_runner.py:677-710`

`_write_json_atomic()` は final path を `os.replace()` できるため、この record には使わない。`orchestrator/campaign/p3_autonomous_workload_trial.py:799-810`

#### outcome 対応

| 物理結果 | evidence record | ledger outcome |
|---|---|---|
| 同一 `build_attempt_id` の ordered WAL が terminal `commit` に到達し、`verify_configs` が verifier-policy artifact の exact ordered setと一致し、execution contract/receipt も一致 | `outcome=accepted`、`constraint_sha256=null` | `accepted` |
| terminal `abort` が candidate-attributable な、非切詰め・既知 kind・構造整合済み witness を持ち、正規化した class が exact 1 件 | `outcome=rejected`、`constraint_sha256=canonical single witness-class digest` | `rejected` |
| witness class が 0 件または複数、切詰め、unknown kind、attempt 帰属曖昧 | record を発行しない。全 witness を黙って 1 件へ選ばない | 当該行以降を `tombstoned`、origin は aborted |
| build error、timeout、empty/parse error、role-invalid、infrastructure、competing tenant、duplicate skip、dry-pass、process crash | record を発行しない | 当該行以降を `tombstoned` |
| valid validation rowが hypothesis を反証 | accepted/rejected record 自体は発行する | 後続行を tombstone suffix とし、formal result は `P6NotDerived`、origin は aborted |

candidate-attributable evidence の閉集合と infra failure の除外は既 P6 契約に従う。`output/insights/2026-08-03_t244-p6-contract/README.md:158-180`

複数 class を一つ選ぶ案は採らない。現 ledger member は `constraint_sha256` を 1 個しか持たず、U-10 の `kmax=1` は単一 class policy として批准されているためである。複数 class を正式に数えるには member schema と Kmax の意味の再裁定が必要であり、この設計では fail-closed に aborted とする。`orchestrator/campaign/reflux_origin_ledger.py:510-530` `output/insights/2026-08-06_t244-u10-budget-values/README.md:281-297`

#### Opened / Sealed への 1 対 1 写像

| result record / plan | `OpenedBatchMember` | `SealedBatchMember` |
|---|---|---|
| `ledger_member.query_ordinal` | `query_ordinal` | 同値 |
| `ledger_member.replicate_ordinal` | `replicate_ordinal` | 同値 |
| `trigger_binding.candidate_wire.encode("ascii")` | `candidate_bytes` | 同値 |
| `physical_result.outcome` | `outcome` | 同値 |
| `SHA256(raw result-evidence record bytes)` | `evidence_digest.sha256` | 同値 |
| `physical_result.constraint_sha256` | `constraint_sha256` | 同値 |
| run plan の `candidate_salt / result_evidence_salt / constraint_salt` | 各 salt | seal 後には存在しない |
| record 不在 | `outcome="tombstoned"`、`evidence_digest=None`、`constraint_sha256=None` | 同値 |

`batch_id` は `BatchSealed.batch_id`、`iteration_index` は先行 `BatchReserved / BatchCommitted` と照合する。member へ存在しない field を存在するかのように写さない。`orchestrator/campaign/reflux_origin_ledger.py:533-562`

`PreparedBatchMember` の三 commitment は、candidate wire/query/replicate、record digest/outcome、constraint の各 opening と run plan の salts から既存 preimage 規則で計算する。`orchestrator/campaign/reflux_origin_ledger.py:672-703` `同:1521-1538`

#### formal consumer

formal consumer は ledger ではなく、P6 の `derive_p6_cut(...)` 契約を実装する trusted consumer である。入力に issued capability、source closure、create-only run plan、`read_sealed_batch()` の結果、全 result-evidence record、ordered WAL を取る。`output/insights/2026-08-03_t244-p6-contract/README.md:116-136`

次をすべて満たした場合にだけ `OriginSealed(aborted=False)` を許可する。

- non-tombstone member ごとに exact 1 record があり、その raw digest が ledger と一致する。
- tombstone member に record がない。
- origin/cell/authority/campaign/workload/descriptor/axis/verifier/environment/admission が capability と一致する。
- query/replicate/wire/outcome/constraint が 1 対 1 写像に一致する。
- base 1 行と mask `0..31` の validation 32 行が固定順で揃う。
- accepted/rejected の WAL 条件が成立する。
- P6 result が `P6Derived` で、marginal set が空でない。
- exact rejected class set、Kmax、floor が一致する。

それ以外は `OriginSealed(aborted=True, constraint_class_sha256s=())` とする。ledger 自体は aborted seal に空 class を要求する。`orchestrator/campaign/reflux_origin_ledger.py:1598-1638`

raw `commit_event` による迂回を残すと formal consumer は恒真な飾りになるため、§4 の capability client が certifiable `OriginSealed` を formal-consumer receipt なしに発行できないことを併せて必須とする。

### (c) 設計が依存する未確認の前提

- exact verifier-policy artifact、witness normalizer、integrity witness の構造化表現、`derive_p6_cut` formal consumer は現時点で未存在である。`output/insights/2026-08-03_t244-p6-contract/README.md:176-180` `同:472-490`
- trusted harness の専用 directory に untrusted role が書けず、同一 UID の任意攻撃者を権限分離できることは未確認である。create-only は上書きを防ぐが、最初の書き手を暗号学的には認証しない。
- physical query は query ordinal 順に逐次実行し、前の record の fsync 前に次 query を始めないことを前提とする。
- `launch_admission_record` の canonical digest 規則と origin capability の serialization は未存在である。

### (d) 採らなかった案と理由

- outer `drive()` の `"certified"/"aborted"` から evidence を後付け合成する案は、attempt と structured witness を失うため採らない。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:582-608`
- `records_by_stage()` を読む案は、legacy verify の先行 record を落とすため採らない。`orchestrator/campaign/wal.py:1406-1427`
- record 内の `issuer` 文字列だけを権限証明にする案は自己申告なので採らない。
- 複数 witness から都合のよい 1 class を選ぶ案は P6 契約違反である。`output/insights/2026-08-03_t244-p6-contract/README.md:197-205`
- tombstone を evidence record として発行する案は、ledger の outcome matrix と「未証明を数えない」境界に反する。`orchestrator/campaign/reflux_origin_ledger.py:682-726`

## 3. 32 mask producer topology

### (a) 現状の現物

- mask の正準順は整数 `0..31` で、各 candidate wire は `encode_wire(TriggerGateIR(mask))` の 5 ASCII bytes である。`orchestrator/campaign/trigger_gate_binding.py:98-108` `orchestrator/campaign/reflux_ir.py:113-128`
- reserve は `iteration_index == iterations_used`、`query_ordinal_start == queries_used`、Bmin/Imax/Qmax を一度に検査し、予約時点で I/Q を消費する。`orchestrator/campaign/reflux_origin_ledger.py:1312-1350`
- P6 は全 validation mask、replicate、順序、予算を最初の validation result より前に一括 commit する必要がある。FSM は一つの open batch しか持たないため、複数 validation batch はこの条件を満たせない。`output/insights/2026-08-06_t244-u10-budget-values/README.md:170-190`
- 同一 candidate bytes でも query/replicate が commitment preimage に含まれるため、base と同一 mask の validation 行を同じ batch に置ける。`orchestrator/campaign/reflux_origin_ledger.py:672-679` `同:1390-1397`

### (b) 設計

fresh origin を必須とし、開始 snapshot は `phase="IDLE" / iterations_used=0 / queries_used=0 / batch_count=0` とする。これにより ordinal の意味を既存探索履歴と混ぜない。各値は `OriginSnapshot` に実在する。`orchestrator/campaign/reflux_origin_ledger.py:588-608`

成功 topology は exact 1 batch、33 member とする。

| member | `iteration_index` | `query_ordinal` | candidate | `replicate_ordinal` |
|---|---:|---:|---|---:|
| source base | 0 | 0 | source の canonical wire `w_s=encode_wire(TriggerGateIR(m_s))` | 0 |
| validation mask `m` | 0 | `1+m` | `encode_wire(TriggerGateIR(m))` | `1` if `m==m_s`、それ以外は `0` |

したがって member 数は 33、candidate bytes の相異数は 32、validation replicate は各 mask について R=1 である。source と同一 mask の validation 行だけが origin-canonical replicate 1 になるが、source 行は validation の R に数えない。ledger は seal 順に candidate bytes ごとの次 ordinal を検査する。`orchestrator/campaign/reflux_origin_ledger.py:1488-1520`

実行順は次に固定する。

1. source candidate、hypothesis、32 mask、順序、salts、operation IDs、最大 reserve attempt 数を create-only run plan に固定する。
2. `BatchReserved(member_row_count=33, query_ordinal_start=0)`。
3. 33 candidate commitments 全部を `BatchCommitted` する。
4. query 0 の source を物理実行する。
5. source が qualifying single-class rejection のときだけ、mask 0→31 を順に実行する。
6. source が accepted/non-applicable、または query `q` で未証明 failure/crash が起きた場合、`q` 以降をすべて tombstone とする。非 tombstone を後ろへ置かない。`orchestrator/campaign/reflux_origin_ledger.py:1488-1516`
7. 全 33 行が non-tombstone かつ formal consumer が `P6Derived` の場合だけ certifiable seal とする。1 行でも tombstone なら `sealed_queries<33` になり、aborted seal 以外を許さない。`orchestrator/campaign/reflux_origin_ledger.py:1598-1638`

reserve 後・commit 前に限り `BatchReservationAbandoned` を使った 1 回の再予約を許す。再予約は `iteration_index=1 / query_ordinal_start=33`、query `33..65`、同じ candidate/validation plan とする。abandon は replicate state を更新せず、replicate count は `BatchSealed` でのみ更新されるため、再予約側の replicate ordinal は成功 topology と同じである。`orchestrator/campaign/reflux_origin_ledger.py:1352-1363` `同:1585-1595`

`BatchCommitted` 後は別 batch へ逃げず、同じ batch を evidence prefix + tombstone suffix で閉じる。tombstone 自体も replicate count を進めるため、post-commit 全量再試行を許すと R と `replicate_ordinal` の意味が分裂する。`orchestrator/campaign/reflux_origin_ledger.py:1513-1520`

D114 の generation 上限 1 は維持する。この topology の「1 generation = 1 drive」は、1 回の trusted batch drive の内部で source と 32 deterministic validation attempts を順次所有する意味とする。現 8c の `drive()` は 1 candidate outcome しか返さないため、これは現在の実行経路では未成立である。`orchestrator/campaign/p3_autonomous_workload_trial.py:1688-1913` `docs/decisions.md:5331-5348`

#### 批准値との照合

- 成功時は I=1、Q=33。
- reserve abandonment 1 回を含む上限は I=2、Q=66。
- Bmin=2、candidate_min=1、F=33、R=1、Kmax=1 には数値上適合する。
- ただし U-10 の `imax=4 / qmax=68` の批准根拠は「探索 2 行 + P6 32 行」をそれぞれ 1 回放棄できる内訳だった。本 topology は exact 33 行を一 batch に統合するため、その内訳とは一致しない。`output/insights/2026-08-06_t244-u10-budget-values/README.md:249-267`

従って現値を変更する提案はしないが、U-10 §7 に従う再計数・再批准が必要である。上限値を同じ `4/68` のまま余裕として残すかどうかも、人間の再批准事項である。`output/insights/2026-08-06_t244-u10-budget-values/README.md:383-391`

### (c) 設計が依存する未確認の前提

- source candidate が 5-bit canonical IR へ束縛済みで、source 観測前に hypothesis と validation plan を固定できること。
- 1 回の trusted drive が、LLM へ 32 回問い合わせず、machine producer として 32 mask を実行できること。
- source と 32 validation が同一 campaign/workload/descriptor/verifier/environment のまま走ること。
- `4/68` をこの新しい event topology の余裕として維持するか、人間の再批准が得られること。

### (d) 採らなかった案と理由

- source batch と validation batch に分ける案は、exact 33 行では source batch が Bmin=2 を満たせず、padding tombstoneか余分な物理 query が必要になる。また validation の一括 commit 条件にも反する。
- 2〜4 batch へ mask を分割する案は、先行 batch の結果開示前に後続 batch を予約できないため採らない。`output/insights/2026-08-06_t244-u10-budget-values/README.md:177-190`
- Bmin を 1 へ下げる案は正しさゲートの緩和なので採らない。
- source の 2 行目を tombstone padding にする案は、下限を実行せず満たす恒真化なので採らない。
- commit 後の crash に対して別の 33 行 batch を追加する案は、tombstone 行も replicate count を進める現 FSMと、批准済み R=1 の意味を分裂させるため採らない。

## 4. origin binding capability

### (a) 現状の現物

`TrialBinding` は `manifest_sha256 / prereg_commit / measurement_head / trial_id / arm / holdout / campaign_id / workload / ycsb_rratio` を持ち、registry seal で caller-constructed value を拒否する。descriptor、origin、cell、authority blob は持たない。`orchestrator/campaign/trial_registry.py:124-149` `同:1071-1112`

registered admission は `binding` を持つが `certifying=False` のままであり、exploratory admission は `binding=None` である。`orchestrator/campaign/trial_registry.py:1132-1248`

8c の `_trial_launch_admission` は descriptor/campaign を再導出して `campaign_id` だけを比較し、元 admission をそのまま返す。`orchestrator/campaign/p3_autonomous_workload_trial.py:635-682`

ledger の公開 API は capability を取らず、caller が直接 `origin_id` を渡せる。`orchestrator/campaign/reflux_origin_ledger.py:3454-3485`

### (b) 設計

文書上の sealed `OriginBindingCapability/v1` は次の exact field を持つ。

- `authority_blob_sha256`
- `source_closure_sha256`
- `origin_id`
- `cell_key`
- `authority_workload` — exact `descriptor_sha256 / records / threads`
- `axis_semantics_sha256`
- `verifier_policy_sha256`
- `environment_contract_sha256`
- `campaign_id`
- `trial_workload`
- `measurement_head`
- `store_scope` — `production` または `fixture`
- issuer seal

発行主体は launch admission gate とし、次を一つの受理判断として行う。

1. `assert_issued_trial_launch_admission` と `assert_rederived_launch_admission` を通す。`orchestrator/campaign/trial_registry.py:1251-1357`
2. mode は `registered-effective`、`binding` は issued `TrialBinding` でなければならない。`explicit-unregistered-exploratory` には production origin capability を発行しない。`orchestrator/campaign/trial_registry.py:1186-1248`
3. `_prepare_campaign_identity` の `PreparedCampaignIdentity.campaign_id` と `binding.campaign_id`、`binding.workload` と `trial_workload` を一致させる。`orchestrator/campaign/p3_autonomous_workload_trial.py:608-632`
4. prepared descriptor の canonical digest、`records / threads`、campaign config の `descriptor_sha256` を authority workload と一致させる。`orchestrator/campaign/p3_autonomous_workload_trial.py:549-605`
5. provisioning receipt、source closure、authority manifest から `origin_id / cell_key / authority_blob_sha256` を再導出する。authority loader の `_Authority.blob_sha256` は実在する。`orchestrator/campaign/reflux_origin_ledger.py:1643-1653` `同:1824-1892`
6. expected axis/verifier/environment を capability に束縛する。physical site で actual environment、WAL verifier config、trigger binding を再確認するまで ledger reserve を許さない。
7. `TrialLaunchAdmission` の serialized record に `origin_binding` を含め、run-start、active run scope、terminal report、result-evidence record が同じ canonical record digest を共有する。現 record が run-start/report 共通 projectionである。`orchestrator/campaign/trial_registry.py:1295-1321`
8. `certifying` は引き続き `False` とする。capability は「この origin の予算を使える」権限であり、P3/P4/certified trial の名乗りではない。`orchestrator/campaign/trial_registry.py:1251-1265`

ledger の production entry point は raw `origin_id` を受け取る形を公開面から外し、issued capability を必須引数にする。client は capability 内の `origin_id` だけを使い、呼出しごとに current authority blob、cell、store scope を再照合する。capability がない場合、read/reserve/commit/seal のどれも行わない。

fixture 規則は次で閉じる。

- `store_scope=fixture` では、完全な fixture store client の明示を必須とする。
- fixture capability だけ渡して client を省略した場合、`_production_store()` へ既定解決せず拒否する。
- production capability と fixture client、fixture capability と production client の組合せを双方拒否する。
- fixture client は現 private `_fixture_store_for_test()` に相当する完全 repo/store を所有し、raw path や部分 store を受け取らない。`orchestrator/campaign/reflux_origin_ledger.py:2969-2985`
- current authority が空である間は production capability を発行できない。

certifiable `OriginSealed` についてはさらに、formal consumer の exact receipt を capability client が要求する。これがないと ledger の「digest を dereference しない」残余を迂回できる。`output/insights/2026-08-06_t244-u10-budget-values/README.md:351-359`

### (c) 設計が依存する未確認の前提

- human provisioning receipt と source closure を launch admission が authority blobから一意に解決する経路は未存在である。
- actual site が campaign identity を変更する場合、site-resolved `campaign_id` も registry binding と一致する必要がある。現 trigger driver は Pegasus で environment tag を search config へ加える。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:327-334`
- Python seal は同一 process 内の issued-value gate であり、暗号署名ではない。module 再束縛や同一 UID の任意改変は保証対象外だが、公開 API の capability 省略と fixture→production fallback は保証対象外へ追い出してはならない。`output/insights/2026-08-06_t244-p3-8c-wiring/s4-adjudication.md:157-165`

### (d) 採らなかった案と理由

- caller が `origin_id` を CLI/API 引数で選ぶ案は V-4 (a) で却下済みである。
- seal のない素 dataclass は別 campaign の予算を消費できるため採らない。
- `assert_campaign_binding()` の campaign ID 比較だけで十分とする案は、descriptor/cell/authorityを束縛しない。現関数も campaign ID しか比較しない。`orchestrator/campaign/trial_registry.py:1702-1711`
- capability を optional にし、`None` なら production client へ落とす案は fixture leak を再導入するため採らない。
- capability を持つだけで `certifying=True` にする案は、D114・P3 FAIL・P4 FAIL の名乗り上限に反する。

## 5. 失敗・crash と receipt 喪失照合

### (a) 現状の現物

既存 phase と受理可能 event は次のとおりである。

- `IDLE → BATCH_RESERVED`: `BatchReserved`
- `BATCH_RESERVED → IDLE`: `BatchReservationAbandoned`
- `BATCH_RESERVED → BATCH_COMMITTED`: `BatchCommitted`
- `BATCH_COMMITTED → RESULTS_PREPARED`: `BatchResultsPrepared`
- `RESULTS_PREPARED → IDLE`: `BatchSealed`
- `IDLE → ORIGIN_SEALED`: `OriginSealed`

各遷移の exact 受理条件は `orchestrator/campaign/reflux_origin_ledger.py:1312-1638` に実在する。

receipt replay は `(origin_id, operation_id, expected_state_commitment, event type, exact payload, event_sha256)` の完全一致である。`orchestrator/campaign/reflux_origin_ledger.py:3099-3120`

### (b) 設計

#### durable recovery envelope

最初の `BatchReserved` より前に、trusted controller は create-only の run-plan/recovery envelope を result-evidence root に置く。これは ledger event ではない。

内容は次を含む。

- issued capability と source closure の digest
- source hypothesis と validation plan の digest
- attempt 0 と reserve-abandon retry 1 の `batch_id`
- iteration/query allocation
- 33 candidate wiresと replicate ordinals
- candidate/result/constraint salts
- 各 event の安定した `operation_id`
- deterministic evidence paths
- 最初の `expected_state_commitment`

この envelope は role projectionへ渡さず、file・parent fsync と read-back を必須にする。ledger snapshot は `BATCH_COMMITTED / RESULTS_PREPARED` では open batch の saltsやmembersを公開せず、reserved phase の最低限しか返さないため、envelope なしでは回収できない。`orchestrator/campaign/reflux_origin_ledger.py:3392-3434`

#### failure/event 対応表

| failure/crash 点 | ledger phase | 回復・終端 |
|---|---|---|
| admission、source closure、actual env照合、run plan 作成の失敗 | `IDLE`、event なし | ledger 無課金。candidate/hypothesis を差し替えず trial を失敗終了する。 |
| `BatchReserved` 呼出し後に receipt 喪失 | 不明 | 同一 `operation_id`、元の `expected_state_commitment`、同一 event payload を再送する。既 commit なら `replayed=True`、未 commit なら CAS が一致する場合だけ初回 commitになる。`orchestrator/campaign/reflux_origin_ledger.py:3161-3216` |
| `BATCH_RESERVED` 中に producer が継続不能 | `BATCH_RESERVED` | `BatchReservationAbandoned`。I/Q は forfeited のまま返さない。receipt 喪失時は同一 request を再送する。`orchestrator/campaign/reflux_origin_ledger.py:1352-1363` |
| `BatchCommitted` 呼出し後に receipt 喪失 | 不明 | exact `BatchCommitted` を再送する。新 operation ID や新 salts を作らない。 |
| physical row が terminal WAL、provenance、result record まで fsync 済み | `BATCH_COMMITTED` | record が連続 prefix にある限り次 ordinalへ進める。 |
| physical row 開始後、result record 作成前に crash | `BATCH_COMMITTED` | 当該 ordinalを最初の missing record とし、その行から batch 末尾まで tombstone。後続実行を再開しない。 |
| valid row が hypothesis を反証 | `BATCH_COMMITTED` | 当該 row を保存し、残りを tombstone suffix、P6NotDerived とする。 |
| `BatchResultsPrepared` receipt 喪失 | 不明 | envelope の salts、result records、tombstone suffix から exact commitments を再構成し、同一 request を再送する。partial result set は ledger が拒否する。`orchestrator/campaign/reflux_origin_ledger.py:1409-1455` |
| `BatchSealed` receipt 喪失 | 不明 | exact opening 全 33 行を再送する。salt/result/constraint が違えば committed operation ID reuse mismatch で停止する。 |
| seal 後に formal consumer が crash | `IDLE` | `read_sealed_batch()` と create-only evidence から consumer を再実行する。ledger event はまだ追加しない。`orchestrator/campaign/reflux_origin_ledger.py:3437-3451` |
| formal result が `P6Derived` | `IDLE` | exact counters/class を持つ `OriginSealed(aborted=False)`。 |
| `NotDerived / NotApplicable / ContractError`、tombstone、evidence mismatch | `IDLE` | `OriginSealed(aborted=True, constraint_class_sha256s=())`。 |
| `OriginSealed` receipt 喪失 | 不明 | 同一 request を再送し、`EventReceipt.replayed` で既 commitを識別する。 |

再送手順は常に envelope の最初の base state から event 順に行う。各 exact resend が返す `resulting_state_commitment` を次 event の expected state とし、途中で別 payload・別 operation・CAS mismatchを観測したら停止する。`EventReceipt` は resulting/current commitment と replay flag をすべて持つ。`orchestrator/campaign/reflux_origin_ledger.py:621-629`

ledger frame 自体の末尾切れは replay が完全 prefix を検査した後に truncateする。consumer が「書けたはず」と推測して補わない。`orchestrator/campaign/reflux_origin_ledger.py:3123-3158`

#### 新 event 型の要否

結論は条件付きで「不要」である。

- reserve 前後の取消は `BatchReservationAbandoned` で表現できる。
- commit 後の未証明結果は tombstone suffix と既存 prepare/seal で表現できる。
- scientific terminal は `OriginSealed(aborted=True/False)` で表現できる。
- receipt 喪失は exact replay/CAS/replayed で閉じる。

ただし durable recovery envelope と create-only result records が無い現状では、既存 6 event だけでは committed/prepared の salts・payloadを再構成できず、crash 設計は閉じていない。足りないのは crash event ではなく、元 request を byte-for-byte 復元する durable material である。新 event を足しても失われた saltsやevidenceを復元できない。

### (c) 設計が依存する未確認の前提

- envelope、WAL projection、provenance projection、result record が ledger runtime と同程度に durable であること。
- capability により同一 origin の production writer が一つに限定されること。
- crash 後も campaign root と evidence root が保持されること。
- filesystem 全損、envelope 消失、同一 UID の悪意ある削除は回復保証外である。この場合は origin が nonterminal に残りうるが、証拠を捏造して certifiable にしてはならない。

### (d) 採らなかった案と理由

- receipt 喪失時に新しい `operation_id` を発行する案は、二重 event と altered continuation を許すため採らない。
- current snapshot の `state_commitment` を新しい expected 値として同じ event を送る案は、元 request の CAS を捨てるため採らない。
- missing row 後に後続 physical row を再開する案は tombstone terminal suffixに反する。
- reserve/commit 消費を crash 時に refund する案は既 no-refund 会計に反する。
- crash を accepted/rejected へ写す案は evidence のない outcome を発行するため採らない。
- `BatchCrashed` 等の新 event は、既存 phase で表現できる意味を重複させるだけで recovery material の欠落を解かない。

## 6. docs 本文の構成案

`docs/phase3-8c-wiring-design.md` は次の節構成とする。

- `# 0. 射程・不変条件・非主張`
  - 実装 wave ではないこと。
  - D201/D183/D114/D211、本番 authority 空、発行 3 条件を固定。
  - P3/P4/cap-lift/production provisioning を名乗らない。

- `# 1. 用語と field-path 規律`
  - manifest、report、campaign config、WAL の同名 field を完全修飾。
  - `descriptor_sha256`、`anomalies`、`campaign_id` の二義化禁止。

- `# 2. source closure`
  - 4 referent の producer bytes 表。
  - `source-closure/v1` schema。
  - captured commit、raw Git blob、provisioning receipt、launch/runtime recheck。
  - axis/verifier artifact 不在による fail-closed。
  - D211 による「一 authority blob」までの名乗り上限。

- `# 3. result-evidence/v1`
  - exact key 集合、canonical bytes、deterministic path。
  - issuer、発行時点、create-only 強制。
  - accepted/rejected/no-record 対応。
  - multiple-class、unknown witness、infra failure の fail-closed。

- `# 4. ledger member mapping`
  - result record → Prepared/Opened/Sealed の 1 対 1 表。
  - salt の出所、record digest、tombstone の扱い。
  - ledger 自身が dereference しない限界。

- `# 5. 32-mask topology`
  - fresh origin。
  - one batch 33 rows の ordinal/replicate 表。
  - precommit、source→mask 0..31 の順序。
  - terminal tombstone suffix。
  - reserve-abandon retry と post-commit non-retry。
  - U-10 再計数・再批准要否。

- `# 6. launch-admission origin capability`
  - capability exact fields。
  - campaign/workload/descriptor/source closure/authority照合。
  - report/run-scope/result-evidence への同一 record projection。
  - production/fixture の型分離と既定解決拒否。

- `# 7. formal consumer と origin terminal`
  - ordered WAL のみを読むこと。
  - P6 4 値 result。
  - certifiable `OriginSealed` の追加 gate。
  - false evidence、multiple class、hypothesis falsification の扱い。

- `# 8. crash/recovery`
  - recovery envelope。
  - 6 event × failure mode 対応表。
  - exact operation replay、CAS、`replayed`。
  - 回復保証外の durability failure。

- `# 9. 発行 3 条件・残余・人間 gate`
  - 各条件の設計上/実装上の状態。
  - axis/verifier artifact、consumer、permitted path、再批准の残余。
  - authority provisioning をまだ許可しない結論。

- `# 10. 却下案と恒真化監査`
  - tombstone padding、last-wins evidence、caller origin、fixture fallback、code self-hash、新 crash eventを却下。
  - 「ledger が受理した＝物理実行した」と書かない。

## 7. 親 brief への不同意

- **(P1): 一部同意、一部不同意。** 4 referent の producer bytes と実在照合を閉じる方針には同意する。一方、「1 authority series 内」と書くと series lifetime の一意性まで保証するように読めるが、現実装に generation/continuity はなく、D211 も repo 内 ever-issued 台帳を拒否する。保証可能なのは一つの manifest/provisioning receiptと同一 authority blob 内までである。`orchestrator/campaign/reflux_origin_ledger.py:1836-1865` `docs/decisions.md:10019-10036`

- **(P2): seal builder だけで閉じる点に不同意。** create-only recordから member を組む builder は必要だが、ledger は evidence digest を dereferenceしないため、それだけでは物理実行 0 件の偽 digest を防げない。formal P6 consumer と、certifiable `OriginSealed` をその receiptに束縛する capability gateまで必要である。`orchestrator/campaign/reflux_origin_ledger.py:205-209` `output/insights/2026-08-06_t244-u10-budget-values/README.md:351-359`

- **(P3): 「4 batch 以下へ割る」に不同意。** validation 全行を最初の result 前に commitする条件と一-open-batch FSMにより、validation 32 行は一 batchに強制される。exact 33 行とBmin=2を同時に満たす形は、sourceも同じ batchへ入れる一 batch 33 行である。これは批准時の I/Q 内訳と異なるため再計数・再批准が必要である。`output/insights/2026-08-06_t244-u10-budget-values/README.md:177-190` `同:249-267`

- **(P4): 同意するが、要件を強める。** capability なしに ledger client が動かないこと、fixture default rejectionには同意する。ただし campaign/workload/descriptorだけでなく、authority blob、cell、source closure、expected axis/verifier/environmentまで capabilityに束縛し、raw public ledger APIから迂回できないことが必要である。現 API は raw `origin_id` を受ける。`orchestrator/campaign/reflux_origin_ledger.py:3454-3485`

- **(P5): 条件付きで同意する。** 既存 6 event で意味上は閉じられるが、「新 event は足さない」を無条件の結論にはできない。durable recovery envelopeがなければ committed/prepared payloadを再構成できない。必要なのは新 eventではなく sidecar materialである、という条件を本文へ明記すべきである。`orchestrator/campaign/reflux_origin_ledger.py:3392-3434`

- **(P6): 同意する。** pin 済み既存文書を変更せず、新規 `docs/phase3-8c-wiring-design.md` を正本とする置き場は妥当である。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-8c-wiring-design/brief.md:64-69`

## 8. 発行 3 条件との対応

| 発行条件 | 本設計が閉じる範囲 | 満たさない残余 |
|---|---|---|
| **V-2 evidence 正本** | exact record schema、canonical bytes、issuer位置、create-only、outcome対応、Opened/Sealed写像、formal consumer責務を設計した。 | verifier-policy artifact、single-class normalizer、structured integrity witness、physical writer、formal consumer、certifiable seal gateは未存在。従って条件は運用上未成立。 |
| **producer topology** | fresh origin、one batch 33 rows、mask順、query/replicate allocation、tombstone suffix、reserve-abandon retryを一意にした。 | 現 8c drive は33物理 attemptを生産しない。批准時内訳と count が異なるため再批准が必要。従って条件は未成立。 |
| **許可された実行経路** | launch admission発行 capability、authority/campaign/workload/descriptor/source closure束縛、production/fixture分離を設計した。 | current admissionにorigin capabilityがなく、public ledger APIはraw originを受け、本番 authorityは空。従って条件は未成立。 |

source closure は上記三条件すべての共通前提である。workload/environment の producer規則は存在するが、axis/verifier の名前付き正本と provisioning receipt がないため、これも現在は未成立である。

従って本設計は「3 条件を満たすための exact contract」を提示するが、3 条件のいずれも実体として成立させない。本番 authority の人間承認 provisioning は引き続き禁止され、71 bytes・origins 0 件を維持する。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-8c-wiring-design/brief.md:19-38`

## 総括

設計上の中心結論は四つである。

1. cell closure は manifest の 4 hashを再計算するだけでは足りず、captured commit の名前付き bytes、provisioning receipt、launch/runtime実成果物まで連結する。ただし axis/verifier正本は未存在であり、現状は発行不能である。
2. V-2 は trusted physical harness が per-query create-only recordを発行し、formal P6 consumerが ordered WALをdereferenceして初めて閉じる。seal builderだけでは閉じない。
3. exact 33 行は `source 1 + mask 0..31` の一 batchに強制される。成功 I/Q は1/33、reserve-abandon retry込み2/66であり、批准時内訳との差について再批准が要る。
4. crash は durable recovery envelopeがあれば既存6 event、exact operation replay、CAS、`EventReceipt.replayed`で閉じられる。envelopeがなければ閉じず、新 eventを増やしても解決しない。

コード、テスト、probe、authority、commitには一切触れていない。すべて未実走の静的設計であり、production provisioning・P3/P4充足・cap引上げを意味しない。