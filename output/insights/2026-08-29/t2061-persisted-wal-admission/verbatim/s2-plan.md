## 総括

`artifact_admission.py` に、COMMIT と同一 attempt の正常な `verify_done` 群および保存済み commit receipt を照合する共通 helper を追加する。  
22 site は既存 chokepoint で一括保護できるが、別に3 siteの lock-only/raw-WAL bypass があり、親 brief の「全 site が chokepoint を通る」は誤りである。  
S6/S8A は chokepoint 強化後なら anomaly COMMIT を受け取れないが、重複判定を廃止するため行単位でも同じ helper を呼ぶ。  
受理集合は、E1かつadmittedでもCOMMIT証拠が不完全・不整合なcampaign/rowを拒否する方向にだけ縮む。最大のriskは既存の合成fixtureが実WALより弱いことである。

## 現物で確認した事実

- `orchestrator/campaign/artifact_admission.py:623-631` の `_claims_certified_execution()` は、COMMITに `contract_sha256` keyがあれば真になるだけである。ただしこれは `:1003-1007` のv1 downgrade検知にも使われるため、「正常なcertification判定」へ意味変更すると malformed claim を見逃して受理集合を広げ得る。既存関数は保守的なclaim検出として残し、新helperを別に置くべきである。
- live経路は `orchestrator/campaign/pipeline.py:1301-1308` で `verify_done` を記録し、`:1322-1333` で `vr.certified` が偽なら即abortする。COMMITは`:1453-1462`でreceiptを発行し、`:1464-1499`、`:1530-1560`の認証後領域だけから出る。
- 保存時は `orchestrator/campaign/wal.py:640-665` がlive receiptを検査して `commit_verification_receipt` をCOMMIT payloadへ埋める。しかし通常v2の保存済みreceipt再検査は行わず、`:1392-1413` の再検査はA-1 non-certifying lockだけである。
- `orchestrator/verifier/commit_receipt.py:188-255` に保存済みreceiptの既存validatorがある。schema、sink、lock SHA、variant、terminal payload SHA、certified verifier evidence、receipt IDを検査する。ただし `operation_identity` は非空文字列としか検査しないため、COMMITの `build_attempt_id` との一致は新helper側で必要である。
- `wal._validate_attempt_topology()` は `orchestrator/campaign/wal.py:1488-1518` でCOMMITとbuild attempt/build receiptを束縛し、`:1521-1556` でverify attemptを束縛するが、verify verdict値やreceiptは検査しない。
- `orchestrator/campaign/campaign_lock.py:49-74` のenforcement closureはexact 24 pathで、`artifact_admission.py`と`commit_receipt.py`は既に含まれる。`s6_sort_sweep.py`と`s8a_trigger_sweep.py`は含まれない。
- `output/campaigns/*` の30 campaignは全てschema/authority/build admissionなしのv1である。全572 `verify_done`の観測値は、正常571件が `certified=true, anomalies=0, verdict=serializable`、異常1件が `certified=false, anomalies=1, verdict=non-serializable`。全459 COMMITは `build_attempt_id`、`contract_sha256`、commit receiptを持たない。
- 実異常例は `output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/runs/wal.jsonl:6-7` のvariant `db4764543546` で、`certified=false, anomalies=1` の後にCOMMITではなくABORTしている。
- repo内 `output/campaigns` に新述語を通せる正例はない。一方、実在する外部official campaign 5件には93 verify/93 COMMITがあり、全件が `certified=true`、`anomalies=0`、`verdict=serializable`、同一attempt、receiptありだった。観測した `commits` は267739〜648899、`aborts`は3255〜251916、全件 `commit_witness.commit_counts == commits`、`batch_commit_counts == 0`。
- 具体的正例は `/work/1/SFC/tanab/b10-backoff-grid-runs5/b10-backoff-grid-20260826T234647Z-783837-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/runs/wal.jsonl:3,5`。同campaignには31 verify/31 COMMITがあり、最初の組はattempt `2c2c739062e508ac73034d3e6534b2fb`、receiptのoperation/variant/tagも一致する。receiptのlock SHA `618ce8...3e2c` は実 `campaign.lock` SHAと一致した。
- `output/insights/2026-08-24_paper-story-a1-paired/result.json:569-604` にも実persisted receiptがあり、同文書に埋め込まれた6 verify/6 COMMITは同じ到達可能値を示す。ただしこれはA-1 non-certifying成果物であり、CERTIFIED_ACCEPTANCE正例には用いない。

## helper 設計

`orchestrator/campaign/artifact_admission.py:623-631` の直後に、例えば次の単一public helperを置く。

```python
def require_persisted_certified_commit(
    records: tuple[object, ...] | list[object],
    commit_record: object,
    *,
    campaign_lock_sha256: str,
) -> object:
    ...
```

入力契約:

- `commit_record` は `records` にidentityで含まれる `STAGE_COMMIT` record。
- raw parserの `WalRecord` と、admission後の `ImmutableWalRecord` の双方を受ける。
- `campaign_lock_sha256` はcallerが同一snapshotから得たlowercase SHA-256。full admissionでは `decision.campaign_lock_sha256`、lock-only consumerでは既存 `campaign_lock_sha256_or_absent(layout)` を使う。
- record非所属、非COMMITなどcaller misuseは `TypeError`。artifact証拠の欠落・不一致は `ArtifactAdmissionError`。
- 成功時は同じ `commit_record` をidentityのまま返す。S6/S8Aが返値をそのままCOMMIT行として扱える。

検査内容:

1. COMMITの `build_attempt_id` が非空exact `str`。
2. COMMITより前にあり、同じvariant・同じattempt IDを持つ `verify_done` が1件以上ある。
3. 各verifyについて以下を全て要求する。
   - `verdict == "serializable"`
   - `certified is True`
   - `type(anomalies) is int and anomalies == 0`
   - `type(commits) is int and commits > 0`
   - `type(aborts) is int and aborts >= 0`
   - `commit_witness` のexact key集合が `commit_counts` / `batch_commit_counts`
   - `commit_counts == commits`、`batch_commit_counts == 0`
   - `workload` がexact `{"tag": non-empty str}`
4. COMMIT payloadから `commit_verification_receipt` を除いたterminal payloadを作り、`commit_receipt.validate_serialized_receipt()` (`commit_receipt.py:202-255`) を `sink_kind="campaign-wal"`、実lock SHA、record.variantで呼ぶ。immutable viewから呼べるよう、MappingProxyType/tupleをJSONのdict/listへ戻す小さい内部変換だけを併設する。
5. validated receiptの `operation_identity == COMMIT.build_attempt_id`。
6. receipt `verifier_evidence` の順序付き `(workload_tag, verdict, certified)` 列を、同attemptのWAL verify列と完全一致させる。`verifier_result_sha256` はWALに完全なVerifyResult preimageがないため再導出しない。
7. COMMIT `verify_configs` はverify tag列の順序保持deduplicateとexact一致させる。repetitionで同tagが複数回receiptへ入る現行pipeline (`pipeline.py:1341-1350`) にも到達可能である。
8. `contract_sha256` とbuild receipt SHAは、helperより前の既存 `wal._validate_attempt_topology()` / `validate_commit_contract_bindings()` に任せ、重複実装しない。

`CommitReceiptError` は `ArtifactAdmissionError` にcause付きで変換する。新しい例外階層、台帳、署名主体は作らない。

## 呼び出し位置と閉包の検証

親 brief の「19 module / 22 site」は二つの数を混同している。

既存 `require_admitted_campaign(...CERTIFIED_ACCEPTANCE)` を通るのは、16 module / 22 siteである。

- `orchestrator/critic/digest.py:1586-1588`
- `orchestrator/campaign/p3_b4_closed_critic.py:740-742,1779-1781`
- `orchestrator/campaign/p3_autonomous_workload_trial.py:3088-3090`
- `orchestrator/campaign/s6_sort_sweep.py:475-476`
- `orchestrator/campaign/backoff_extended_sweep_report.py:459-463`
- `orchestrator/campaign/backoff_sweep_report.py:57-59`
- `orchestrator/campaign/backoff_overthrottle.py:145-149`
- `orchestrator/campaign/p3_b4_wiring_probe.py:1475-1477`
- `orchestrator/campaign/p3_s4_loop_sort.py:546-548,743-745`
- `orchestrator/campaign/autonomous_trial_completeness.py:4423-4425,4912-4914,4959-4961`
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:1088-1090`
- `orchestrator/campaign/p3_s4_loop.py:1240-1242,1576-1578,1791-1793`
- `orchestrator/campaign/s8a_trigger_sweep.py:577-578`
- `orchestrator/campaign/replay.py:184-186`
- `orchestrator/campaign/layer3_report.py:685-688`
- `orchestrator/campaign/p3_s4_red.py:191-193`

これらはすべてpublic closure `artifact_admission.py:1176-1192` から `_require_admitted_campaign():1141-1173` へ入る。`:1157` のepoch gate後、`:1158-1164` のview生成前に、全COMMITをhelperへ通す。epoch拒否の既存例外優先順位を維持し、HISTORICAL_RAWには発火させない。

追加で、次の3 production siteは `CERTIFIED_ACCEPTANCE` を指定するがlock-only APIを使い、WALを独自に読む。

- `orchestrator/campaign/backoff_requested_us.py:450-469`
- `orchestrator/campaign/s1_report.py:385-424`
- `orchestrator/campaign/s8b_oracle_report.py:553-558,1737`

したがってproduction closureは19 module / 25 literal purpose siteであり、「全てが `_require_admitted_campaign()` を通る」は反証される。3 bypassは以下へ直接結線する。

- backoff reference: `_reference_records():444-501` で全COMMITをhelperへ通し、`:573-576` と`:615-622` の弱いcertified/receipt独自判定を削る。既存consumer例外面に合わせて `RuntimeError` へ変換する。
- S1: `_sample_from_segment():294-341` にlock SHAを渡し、一意COMMITをhelperへ通す。失敗は `persisted_certification_invalid` issueとしてsampleを不受理にする。
- S8B: `_assess_window():1375-1628` にlock SHAを渡し、一意COMMITをhelperへ通す。失敗はrowの `protocol_violation` にする。

(P2) はS6/S8Aについては偽である。chokepointが全COMMITを検査すれば、1 variantだけにanomaly COMMITがあるcampaignもview発行前に拒否される。ただし3 bypassにはchokepointが届かない。またD1246の重複排除を満たすため、S6 `:438-469` とS8A `:540-571` はpayloadだけでなくrecordを保持し、COMMITがある場合は同じhelperの成功を `certified=True` の条件にする。

(P1) は支持する。新moduleならexact 24 path外に実装が出るうえ、closureへ追加すると `campaign_lock.py:221-233` のexact key集合が25件になり、既存v2 authorityがcodec段階で全拒否される。`artifact_admission.py` 内なら既存24-path membershipを変えずに済む。

## 束縛する述語と到達可能性の実測

| field | 採用する述語 | 到達可能性 |
|---|---|---|
| verify `build_attempt_id` | COMMIT attemptとexact一致 | external official 93/93で一致 |
| `verdict` | exact `"serializable"` | official 93/93、A-1 embedded 6/6 |
| `certified` | `is True` | official 93/93。repo内実負例はfalse |
| `anomalies` | exact int 0 | official 93/93。repo内実負例は1 |
| `commits` | exact int、正 | official 267739〜648899 |
| `aborts` | exact int、0以上 | official 3255〜251916 |
| `commit_witness` | exact 2 key、commit数一致、batch 0 | official 93/93 |
| `workload.tag` | 非空str | officialは全件`legacy` |
| COMMIT `verify_configs` | verify tag列の順序保持deduplicateと一致 | official 93/93、live producerも同じ順で生成 |
| receipt schema/sink | v1 / `campaign-wal` | official 93/93 |
| receipt lock | 実campaign.lock SHAと一致 | named B10正例で一致 |
| receipt variant | COMMIT record.variantと一致 | official 93/93 |
| receipt operation | COMMIT attempt IDと一致 | official 93/93 |
| receipt terminal hash/ID | 既存validatorで再計算一致 | writerの保存時契約は`wal.py:646-665` |
| receipt verifier evidence | WAL verifyのtag/verdict/certified列と完全一致 | official 93/93 |

`verifier_result_sha256` の値は64桁hexとして既存validatorが検査するが、WALにその完全preimageがないため再計算条件にはしない。到達不能な述語は採用しない。

## 受理集合の変化

変更前のCERTIFIED_ACCEPTANCEは、admission/epoch/topology/contract bindingが通れば、COMMITに対応するverify verdictや保存済みreceiptが不完全でも通る。

変更後は次の集合だけになる。

```text
旧受理集合
∩ 全COMMITが同一attemptの正常verify列を持つ
∩ 全COMMITが実lock/variant/attempt/terminal payloadに束縛した有効receiptを持つ
```

具体的に新たに拒否されるもの:

- `test_artifact_admission._new_schema_campaign()` が現在作るbuild_start→build_done→COMMITだけのE1 fixture。
- `test_bench_first_real_wal._upgrade_to_fixed_e1()` が作る、verifyは正常だがreceiptのないE1 fixture。
- S6/S8Aの、receiptはあるがverify_doneのない合成screen fixture。
- anomalous verifyとCOMMITを同一attemptへ入れるA-01反例。
- receipt欠落、別attempt、別variant、別lock、別terminal payload、WAL verify列とreceipt evidenceが不一致なcampaign。

変わらないもの:

- COMMITがない空campaign。
- anomaly verifyの後にABORTし、COMMITしないvariant。
- HISTORICAL_RAW。
- 既にoverlay/E0/epochで拒否されるrepo内30 campaign。
- named B10正例を含む外部official 5 campaign。

広がる変更は含めない。特に `_claims_certified_execution()` を「valid receiptがある場合だけ真」に変える案は、v1 downgrade検知を弱め得るため却下する。

## 既存 fixture / test への波及 (全件)

追随が必要:

- `orchestrator/tests/test_artifact_admission.py:414-494` の `_new_schema_campaign()`。正常verifyとreceipted COMMITを既定fixtureへ加える。影響nodeは`:1137`、`:1157`、`:1198`。`:1243` のcurrent-closure-unavailableはepochが先行するため期待変更不要。
- `orchestrator/tests/test_bench_first_real_wal.py:85-137,160-213`。最終v2 lock確定後にbaseline COMMIT receiptを発行する。影響nodeは`:244`、`:279`、`:319`。
- `orchestrator/tests/test_critic.py:592-631`。`_write()` とretry fixtureに正常verifyの全必須fieldを足す。影響nodeは`:637,:662,:678,:699,:712,:727,:795`。`:740-758` の「committed attemptにverifyなし」は、空signal正例からadmission拒否負例へ期待を変更する。
- `orchestrator/tests/test_s6_sort_sweep.py:647-707,710-786`。certified variantにattempt-bound verifyを追加する。
- `orchestrator/tests/test_s8a_trigger_sweep.py:856-916,919-999`。S6と同じ追随を行う。
- `orchestrator/tests/test_s1_report.py:94-123`。sessionごとのattempt IDをbuild/verify/COMMITへ伝播し、各 `verify_configs` tagのverify recordをreceiptと同じ順で出す。共有 `_fixture():134-194` のcall siteは`:343,:356,:366,:376,:402,:428,:477,:487,:508,:517,:529,:541,:558,:585`。
- `orchestrator/tests/test_s8b_oracle_report.py:556-680` の `_verify()` / `_trial()`、`:764-847` のmanual/default pipeline。正常COMMITは `append_legacy_raw_commit()` でなく既存 `log_receipted_commit()` を用いる。custom malformed pipelineは負例用raw注入のまま残す。共有fixtureへの波及が広いため同module全走を親受入対象にする。
- `orchestrator/tests/test_backoff_requested_us.py` には現状 `load_reference_binding()` の正負WAL fixtureがない。共通helper呼出しを外した変異を殺す、helper例外伝播の小さいunit testを追加する。

追随不要:

- `orchestrator/tests/conftest.py` は全2959行の識別子検索でWalRecord、COMMIT、verify_done、admission campaign fixtureを持たない。
- `orchestrator/tests/certified_writer_fixtures.py:86-276,279-306` はqualification/source fixtureで、campaign WALを作らない。
- `orchestrator/tests/commit_receipt_support.py:111-126` は必要なreceipt発行機構を既に持つ。`:207-219` の `append_legacy_raw_commit()` はlegacy/負例注入用として残し、関数自体を強化しない。
- `orchestrator/tests/test_campaign.py:1194,2101,2138,2154,2242-2243,2299,2785-2788` はWAL writer/recoveryのlegacy raw負例でありCERTIFIED_ACCEPTANCEへ渡さない。
- `orchestrator/tests/test_t1286_commit_receipt.py:146,599` はreceipt sink自身のlegacy/negative testであり追随不要。
- `orchestrator/tests/test_critic.py:779` は明示的HistoricalCampaignView fixtureなので追随不要。
- `test_p3_autonomous_workload_trial.py:212-215,5656-5659`、`test_p3_b4_closed_critic.py:261-264,1905-1908`、loop三系の `_critic_view()` は空WALまたはABORTのみを扱い、COMMITがない限り新helperの対象外。
- `test_s1_9pair_figure_provenance.py` の実campaignはE0拒否確認であり、新helper到達前に止まる。
- `test_backoff_consumers.py` と `test_autonomous_trial_completeness.py` はadmission関数をfake viewへ差し替えるconsumer単体testで、persisted gate fixtureではない。

## 凍結 bytes への影響

- `_KNOWN_REPIN_ROWS` は `orchestrator/campaign/t080_freeze_migration.py:90-102` でS6/S8Aの歴史SHAを記録する。
- 実検証は `_basis_blob():874-880` が `migration_basis_commit:path` のblobを読み、`_verify_known_closure():1365-1381` がreceiptの `migration_blob_sha256` と比較する。live working-tree fileの現在SHA比較ではない。
- よって `s6_sort_sweep.py` / `s8a_trigger_sweep.py` の編集は安全で、`_KNOWN_REPIN_ROWS`、T-080 receipt、known_axes/holdout freezeを再pinしてはならない。
- `FROZEN_MANIFEST` は `orchestrator/tests/test_frozen_artifacts.py:41-88` のexact 23 output pathであり、Python sourceは0件。`:90-117` がkey集合も固定する。本変更ではその23 bytesを一切触らない。
- `output/s8b-freeze/**`、`output/s1-freeze/**`、`FROZEN_MANIFEST`、T-080 receiptの変更は実装計画から明示的に除外する。
- `artifact_admission.py` 編集でfuture campaignのE1表示IDは変わるが、D1163後の `artifact_admission.py:847-865` はcurrent closureの可用性だけを要求する。既存campaignのrecorded 24-path mapとの一致は要求しない。

## 実装手順 (file:line 粒度・順序つき)

1. `artifact_admission.py:35-40` に `STAGE_VERIFY_DONE` と既存receipt validator/constantsをimportする。
2. `artifact_admission.py:623-631` 直後へ共通helperとimmutable JSON thaw内部関数を追加する。既存 `_claims_certified_execution()` は変更しない。
3. `artifact_admission.py:1157-1164` でCERTIFIED_ACCEPTANCEの場合だけ、records中の全COMMITをhelperへ通してからview/capabilityを発行する。
4. `backoff_requested_us.py:444-501` をhelperへ結線し、`:573-576,:615-622` の弱い独自認証を削る。receipt IDの出力自体 `:688` は維持する。
5. `s1_report.py:294-341,423-482` へcampaign lock SHAを伝播し、session COMMITをhelperへ通す。
6. `s8b_oracle_report.py:1375-1628,1737,1964-1969` へlock SHAを伝播し、committed windowをhelperへ通す。
7. `s6_sort_sweep.py:438-469` と `s8a_trigger_sweep.py:540-571` のstage mapをrecord保持へ変え、COMMIT時のcertified判定をhelper成功へ置換する。
8. 前節のfixtureを追随させる。正常fixtureは必ず既存 `commit_receipt_support.log_receipted_commit()` を使い、raw receipt dictを手作りしない。
9. `test_artifact_admission.py:1137` 付近へ共通helper正負テスト、S6/S8A各testへ行単位配線test、3 bypass consumerへ伝播testを追加する。
10. closure 25 site、述語、実artifact値域、受理集合差を新insightへ記録する。新台帳や署名主体は作らず、凍結成果物は変更しない。
11. 親が関連pytest、`check_codex_agents.py`、`check_docs.py`、commit後provenance監査を実行する。本プラン起草ではpytestを実走していない。

## 負例の署名と通る正例

helperの負例署名:

| 入力 | helper結果 |
|---|---|
| COMMITに同attempt verifyなし | `ArtifactAdmissionError` |
| verify `certified=False` | `ArtifactAdmissionError` |
| verify `anomalies=1` またはbool/float | `ArtifactAdmissionError` |
| verify `verdict != serializable` | `ArtifactAdmissionError` |
| commit witness欠落、不一致、batch非0 | `ArtifactAdmissionError` |
| receipt欠落・schema/sink/ID不正 | `ArtifactAdmissionError`, cause=`CommitReceiptError` |
| receipt lock/variant/terminal payload不一致 | 同上 |
| receipt operationがCOMMIT attemptと不一致 | `ArtifactAdmissionError` |
| receipt evidence列とWAL verify列が不一致 | `ArtifactAdmissionError` |
| helperへ非COMMITまたはrecords外recordを渡す | `TypeError` |

full chokepointでは上記がそのまま `require_admitted_campaign()` から送出される。S1/S8Bはreport issueへ、backoff referenceは`RuntimeError`へ変換する。

通る正例は実在する `b10-backoff-grid-silo-balanced-sweep-9ded73c4`。`runs/wal.jsonl:3,5` のvariant `10dee7fb5230` は同attempt、正常verify、witness、`verify_configs=["legacy"]`、実lock/variant/attempt/terminal payloadに束縛したreceiptを持つため、新helperを通る。

## 変異事前登録候補

| 変異 | 変異させるfile:line | 期待して赤になるpytest node id |
|---|---|---|
| `certified is True` 検査を除去 | `artifact_admission.py:623-631`直後の新helper | `orchestrator/tests/test_artifact_admission.py::test_persisted_commit_gate_rejects_invalid_evidence[certified-false]` |
| `anomalies == 0` を除去 | 同helper | `orchestrator/tests/test_artifact_admission.py::test_persisted_commit_gate_rejects_invalid_evidence[anomalies-positive]` |
| verify/COMMIT attempt一致を除去 | 同helper | `orchestrator/tests/test_artifact_admission.py::test_persisted_commit_gate_rejects_invalid_evidence[verify-attempt-mismatch]` |
| durable receipt validator呼出しを除去 | 同helper | `orchestrator/tests/test_artifact_admission.py::test_persisted_commit_gate_rejects_invalid_evidence[receipt-terminal-mismatch]` |
| receipt operation一致を除去 | 同helper | `orchestrator/tests/test_artifact_admission.py::test_persisted_commit_gate_rejects_invalid_evidence[receipt-operation-mismatch]` |
| WAL verify列とreceipt evidence列の比較を除去 | 同helper | `orchestrator/tests/test_artifact_admission.py::test_persisted_commit_gate_rejects_invalid_evidence[receipt-workload-mismatch]` |
| chokepointで先頭COMMITだけ検査 | `artifact_admission.py:1157-1164` | `orchestrator/tests/test_artifact_admission.py::test_certified_view_checks_every_commit[second-commit-invalid]` |
| S6またはS8Aの行単位helper呼出しを除去 | `s6_sort_sweep.py:452-456` / `s8a_trigger_sweep.py:554-558` | `orchestrator/tests/test_s6_sort_sweep.py::test_rows_use_common_persisted_commit_gate[s6]`; `orchestrator/tests/test_s8a_trigger_sweep.py::test_rows_use_common_persisted_commit_gate[s8a]` |

parametrize IDはすべてASCIIで固定する。

## 親 brief の誤りと scope 外候補

親 brief の誤り:

- 表には25 siteが載っているのに「22 site」と集計している。正しくは22 full-admission siteと3 lock-only/raw-WAL siteである。
- `backoff_requested_us.py`、`s1_report.py`、`s8b_oracle_report.py` は `_require_admitted_campaign()` を通らない。
- (P2) の「S6/S8Aはchokepointだけでは1 variant anomaly campaignを通す」は、全COMMIT検査をchokepointへ置く設計では偽。ただし3 bypassがあるため「chokepointだけで全consumerを保護できる」も偽である。
- repo内 `output/campaigns` に通る正例は存在しない。正例は外部official B10 campaignを名指す必要がある。
- (P3) は正しく、fixture波及はartifact admissionだけでなくcritic、S1、S8B oracleまで届く。

scope外候補として実装に入れないもの:

- 将来consumerの自動登録や汎用proof framework。
- 新しいreceipt schema、台帳、署名主体。
- `_CERTIFIED_VIEW_TOKEN` の外部capability化。
- `current-closure-unavailable` の撤去。
- guided/non-certifying/A-1/A-2固有protocolの再設計。
- producer直後のsanity表示や一般の `wal.replay()` 全体を新helperへ強制する変更。これらを一括変更するとD1246の「実在するcertified admission consumer」から一般proof制度へ広がる。