## 前提

- [実測] 指定された 4 文書を順番どおり読了し、base worktree のコードを静的に追った。sandbox は read-only なので pytest は実行していない。以下に「緑」の主張はない。
- [実測] B1 は marker・claim・主台帳の read 側と process-local capability だけで閉じられる。既存 marker document、claim document、`ledger.jsonl`、`attempt-ledger.jsonl` の書出し経路は変更不要である。`orchestrator/campaign/s8b_holdout_admission.py:4228-4271,4443-4516`

## T-2107 — 分類規則の実測

| 分類入力・分岐 | 実体 |
|---|---|
| [実測] 計測前競合 | post-measurement ラダーとは別に、pre-probe が競合を返すと直ちに `competing_process` で終了する。これは親 P1 の「該当ラダーだけ」という読みから漏れていた。`orchestrator/campaign/s8b_floor_campaign.py:6077-6090` |
| [実測] probe の確定不能 | timeout、OS error、曖昧な `pgrep` 結果は理由へ丸めず `CampaignAbort` になる。`orchestrator/campaign/s8b_floor_campaign.py:1681-1720` |
| [実測] 計測例外 | `RuntimeError` と `subprocess.TimeoutExpired` だけが `measure_error` へ射影される。それ以外は分類せず伝播する。`orchestrator/campaign/s8b_floor_campaign.py:6092-6103` |
| [実測] post-probe | 計測成否より優先され、`probe_after["competing"]` が最優先の `competing_process` になる。`orchestrator/campaign/s8b_floor_campaign.py:6103,6147-6153` |
| [実測] throughput | `ScalePoint.rep_observations` の exact shape、return code、perf counter 完備性から qualified throughput だけを選ぶ。`orchestrator/campaign/s8b_floor_campaign.py:1891-1969` |
| [実測] exec failure | `ScalePoint.notes` の固定 regex `(\d+)/\d+ reps failed to execute` から導出する。`orchestrator/campaign/s8b_floor_campaign.py:1877-1888,1963-1968` |
| [実測] rep integrity | rep index、return code、counter status、missing event、perf raw、throughput の全条件から件数を導出する。`orchestrator/campaign/s8b_floor_campaign.py:1924-1968` |
| [実測] partial / performance / valid | `assess_session()` が本数、型、有限正値、CV 閾値から純粋に返す。`orchestrator/campaign/s8b_floor_stats.py:96-164` |
| [実測] reason precedence | post競合 → measure例外 → 全rep失敗 → 一部exec失敗と完全出力の矛盾 → rep integrity partial → `assess_session` の partial/performance/valid、の固定ラダーである。`orchestrator/campaign/s8b_floor_campaign.py:6147-6163` |
| [実測] 閉表照合 | 決まった理由が protocol の `allowed_excluded_reasons` に無ければ出力せず abort する。`orchestrator/campaign/s8b_floor_campaign.py:5914-5917,5930-5936,6182-6190` |
| [実測] reason 以外の停止 | reservation 喪失、binary hash 不一致、run command 不一致、stats 内部不変条件違反も session reason へ変換せず停止する。`orchestrator/campaign/s8b_floor_campaign.py:6017-6047,6066-6075,6113-6121,6136-6145` |

- [実測] したがって「固定規則で決まる」は real だが、「`6147-6163` のラダーだけで決まる」は refuted である。pre-probe の早期分類と、分類不能を abort にする分岐も authority policy の意味に含める必要がある。`orchestrator/campaign/s8b_floor_campaign.py:6077-6090,6147-6163`

## T-2107 — `session_cv_max` の権威

- [実測] `assess_session()` は `session_cv_max` を引数で受け、decimal 文字列を `Fraction` に変換し、`CV > threshold` のときだけ `performance_anomaly` を返す。同じ throughputs でも閾値が違えば理由が変わるため、閾値は分類 policy の意味入力である。`orchestrator/campaign/s8b_floor_stats.py:96-106,126-164`
- [実測] この値は実行時の自由入力ではない。現在値 `"0.10"` は「承認済み標本設計 pin」と明記された module 定数である。`orchestrator/campaign/s8b_approved.py:21-24,51-58`
- [実測] protocol builder はその定数を必ず document に焼き、protocol validator も別の承認 pin `"0.10"` と exact equality を要求する。`orchestrator/campaign/s8b_floor_campaign.py:1306-1327`, `orchestrator/campaign/s8b_floor_contract.py:90-101,490-508`
- [実測] `_Runner` が読む値は検証済み protocol の `reps` と `session_cv_max` である。caller が session ごとに選び直す入口はない。`orchestrator/campaign/s8b_floor_campaign.py:5913-5917,6136-6140,7142-7164`
- [実測] `reps` も partial/valid の分類を左右し、承認値へ pin されている。authority document を自己完結させるなら `session_cv_max` だけでなく `reps` の値または凍結 protocol field への束縛も必要である。`orchestrator/campaign/s8b_floor_stats.py:129-156`, `orchestrator/campaign/s8b_floor_contract.py:490-502`

## T-2107 — scheduler authority との比較

| 分類 | `authority_policy_document()` の内容 |
|---|---|
| [実測] identity | schema version と `AUTHORITY_ID` を含む。`orchestrator/campaign/s8b_scheduler_accounting.py:40,65-70` |
| [実測] 証拠取得 policy | exact command argv、capture side、必須 field、時刻 field を含む。いずれも人間が選んだ policy 値である。`orchestrator/campaign/s8b_scheduler_accounting.py:71-85` |
| [実測] 閾値 | raw record の上限 `1 MiB` を policy bytes に含む。`orchestrator/campaign/s8b_scheduler_accounting.py:41,71-76` |
| [実測] receipt identity | receipt schema、event、source、failure reason の閉集合を含む。`orchestrator/campaign/s8b_scheduler_accounting.py:32-48,86-91` |
| [実測] 環境実測値 | observed exit-code counts を policy bytes に含む。ただし意味対応表ではないと明記されている。`orchestrator/campaign/s8b_scheduler_accounting.py:50-62,92-95` |
| [実測] 意味対応 | exit code から failure reason への規則は空配列として明示する。`orchestrator/campaign/s8b_scheduler_accounting.py:59-62,92` |
| [実測] 含めない閾値 | 同じ module の `RECEIPT_MAX_BYTES=64 KiB` と `REGISTRY_MAX_BYTES=16 MiB` は policy document に入らない。`orchestrator/campaign/s8b_scheduler_accounting.py:42-43,65-96` |
| [実測] 含めない実装詳細 | parser 本体、path、lock、canonical JSON 実装、`QSTAT_REQUEST_ID_RE` は document に入らない。policy document は全 module 定数の dump ではなく、権限が名乗る意味境界を選んでいる。`orchestrator/campaign/s8b_scheduler_accounting.py:24-31,65-102` |

- [実測] この先例は「人間選択値や閾値を policy bytes に入れると機械導出でなくなる」という読みを支持しない。既に選択済みの定数を canonical document へ射影し digest を求める操作自体は機械導出である。`orchestrator/campaign/s8b_scheduler_accounting.py:65-102`
- [実測] 親 P1-b の「`session_cv_max` を埋めると protocol 世代ごとに authority digest が変わる」は強すぎる。同じ閾値なら protocol の他 field が変わっても authority digest を変える必要はなく、閾値を変えたときだけ分類 policy が実際に変わる。現在値は既に `"0.10"` へ凍結済みである。`orchestrator/campaign/s8b_approved.py:51-58`, `orchestrator/campaign/s8b_floor_contract.py:500-502`

## T-2107 — 3 択の結論

- [実測] 結論は **(i) 機械導出できる** である。
- [実測] authority policy の意味 field は、既存の reason 定数、probe 規則、例外集合、rep evidence 射影、`FORMULA_ID`、`assess_session`、承認済み `reps`、承認済み `session_cv_max="0.10"`、固定 precedence から決められる。新しい数値や reason を人間が選ぶ必要はない。`orchestrator/campaign/s8b_floor_attempt_launcher.py:25-30,378-385`, `orchestrator/campaign/s8b_floor_campaign.py:1877-1969,6077-6163`, `orchestrator/campaign/s8b_floor_stats.py:50-60,126-164`
- [推測] policy document には単に「閾値は protocol 引数」とだけ書くより、現在の承認値 `"0.10"` と source field `protocol.session_cv_max` の両方を入れるのが安全である。これなら authority digest 単体でも現在の理由境界が分かり、将来この閾値を変えるときだけ新 policy digest が必要になる。
- [実測] D1032 の「性能量に到達する前に理由を固定する」は、分類規則、閉 reason 集合、閾値を事前に canonical policy bytes へ固定し、その digest と protocol digest を分類 receipt に束縛すれば満たせる。現在の registry は classification receipt に `authority_id`、`authority_policy_sha256`、外部証拠 digest を output observation 前に永続化する形を既に持つ。`orchestrator/campaign/s8b_floor_attempt_launcher.py:589-612`, `orchestrator/campaign/s8b_attempt_registry.py:1289-1399`
- [実測] 現時点でユーザーへ決定を返すべき未決値はない。将来 `session_cv_max` 自体を変更する場合は人間所有の protocol policy 変更になるが、それは今回の production 定数の値を決めるための新判断ではない。`orchestrator/campaign/s8b_approved.py:21-24,51-58`

## B1 — `CellHoldoutAdmission` の射影

- [推測] `CellHoldoutAdmission` の末尾へ、default なしで次を追加する。

```python
measurement_generation_claim_digest: str | None
```

- [実測] `None` は必要である。inspector は measurement-generation ledger なら claim digest を再導出し、legacy ledger なら明示的に `None` を使って同じ `_CellState` を構築している。`orchestrator/campaign/s8b_holdout_admission.py:5845-5869,5918-5926,6227-6253`
- [推測] default は付けない。全 issuer に current/legacy の選択を明示させ、field を渡し忘れた構築を静かに legacy 扱いしないためである。
- [実測] 構築式は repo 全体で 2 箇所だけで、どちらも全 field を keyword で渡している。位置引数構築は 0 件である。`orchestrator/campaign/s8b_holdout_admission.py:1793-1819,6227-6253`
- [推測] fresh と resume は共通の `finalize_floor_holdout_admissions()` を通るので、`1795-1801` では `row["measurement_generation_claim_digest"]` を渡す。fresh/resume の値はどちらも non-`None` SHA-256 である。`orchestrator/campaign/s8b_holdout_admission.py:1704-1740,1770-1819`
- [推測] inspector 再構築の `6229-6235` では、`current_measurement_generation` なら `claim_identities[cell_id]`、legacy なら `None` を渡す。`orchestrator/campaign/s8b_holdout_admission.py:5897-6029,6227-6253`
- [実測] 追加で直接壊れる constructor はこの 2 箇所だけである。型名の production/test 外部構築、`asdict`、`astuple`、位置引数呼出しは見つからない。token は `_cell_states[id(token)]` で process-local state に結び付けられている。`orchestrator/campaign/s8b_holdout_admission.py:389-404,434-435,1793-1819`
- [推測] frozen slots dataclass の equality/hash/repr shape は変わるが、marker、claim、台帳、result の serialized bytes には使わない。書出し bytes は不変である。

## B1 — marker capability API

- [推測] public API の署名を次で固定する。

```python
def validate_floor_attempt_consumption_marker(
    admission: CellHoldoutAdmission,
    *,
    attempt_id: str,
) -> FloorAttemptConsumptionMarker:
    ...
```

- [推測] `FloorAttemptConsumptionMarker` と `validate_floor_attempt_consumption_marker` は `__all__` に追加する。既存 public surface は削除しない。`orchestrator/campaign/s8b_holdout_admission.py:47-82`
- [推測] `FloorAttemptConsumptionMarker` は通常 constructor を持たない exact classとし、private `__slots__` に process-local seal と private identity record だけを保持する。外へ marker path、raw bytes、canonical document、claim document、台帳 row は見せない。
- [推測] private identity は最低でも canonical admission root、schema、generic claim digest、attempt ID、campaign run ID、manifest digest、run relative path、cell ID、freeze holdout key、configuration ID を持つ。current の generic claim digest は `measurement_generation_claim_digest`、legacy は `cell_effect_digest` である。
- [推測] capability は immutable かつ再利用可能にする。process crash 後は serialize/reloadせず、再構築した admission tokenから marker を再検証して新しい capability を得る。
- [推測] adapter から raw identity を読ませないため、admission module 内に次の private assertion を置く。

```python
def _assert_floor_attempt_consumption_marker_capability(
    capability: FloorAttemptConsumptionMarker,
    *,
    root: Path,
    claim_digest: str,
    attempt_id: str,
    campaign_run_id: str,
    manifest_sha256: str,
    run_relpath: str,
    cell_id: str,
    freeze_holdout_key: str,
    configuration_id: str,
) -> None:
    ...
```

- [推測] この assertion は exact type、process-local seal、全 identity の equality だけを検査する。path や document の再導出・再読込は admission 側の public validator に一本化する。

## B1 — capability 発行時の完全再導出

| 対象 | 実装案 |
|---|---|
| [推測] admission token | `_cell_state(admission)` で module-issued token か確認し、token の `measurement_generation_claim_digest` が state と一致することを要求する。`orchestrator/campaign/s8b_holdout_admission.py:389-404,4228-4237` |
| [推測] attempt membership | `attempt_id` を `_require_text` に通し、`state.attempt_ids` に含まれることを要求する。`orchestrator/campaign/s8b_holdout_admission.py:4233-4237` |
| [推測] expected marker | `_floor_attempt_document_for_state()` を単一 dispatch に使う。current は既存 `_canonical_measurement_generation_floor_attempt_document()`、legacy は既存 `_canonical_floor_attempt_document()` を通る。`orchestrator/campaign/s8b_holdout_admission.py:4274-4301,4443-4516` |
| [推測] canonical path | expected marker から `_floor_canonical_marker_path()` を呼ぶ。current は `measurement-generation-consumed/`、legacy は `consumed/` になる。adapter 側では path を導出しない。`orchestrator/campaign/s8b_holdout_admission.py:4519-4546` |
| [推測] safe read | admission root lock 下で `_read_canonical_document()` を使い、regular non-symlink、exact 1 canonical JSON line を要求する。`orchestrator/campaign/s8b_holdout_admission.py:589-608,1228-1241` |
| [推測] claim | `_canonical_floor_attempt_ledger_row()` を単一 dispatch にする。current は exact 13-key marker、current claim schema/key集合、attempt coverage、entry kind、seamsを検証する。`orchestrator/campaign/s8b_holdout_admission.py:4549-4557,4675-4759` |
| [推測] current generation identity | current helper 内で既存 `_measurement_generation_claim_identity(claim)` も呼び、`measurement_generation_id` が roleとcampaignから再導出した値か、generation digest・cell effect・claim digest が一貫するかを確認する。現 helper は claim digestを再計算するが generation ID 自体の再導出を直接呼んでいないため、ここは受理を狭める補強になる。`orchestrator/campaign/s8b_holdout_admission.py:835-933,4696-4739` |
| [推測] 主台帳 | claim digestに一致する current main row が exactly 1 件、exact key集合で、claimから組み立てた expected rowと完全一致することを要求する。`orchestrator/campaign/s8b_holdout_admission.py:4761-4807` |
| [推測] marker identities | claim・主台帳から既存 canonical builder を再度呼び、disk marker と完全一致させる。marker自身の fieldを権威にしない。`orchestrator/campaign/s8b_holdout_admission.py:4808-4824` |
| [推測] capability identity | 完全一致した canonical marker から private identityを作り、rootも含めて seal する。別root、別generation、別attempt、別slotへの移植を拒否する。 |
| [実測] attempt ledger | markerだけが存在し attempt-ledger append前にcrashする cut-6 は既存の有効状態である。capability validatorは `attempt-ledger.jsonl` を要求しない。legacy/currentの cut-6 validatorも残す。`orchestrator/campaign/s8b_holdout_admission.py:4251-4269,4827-4924` |

## B1 — adapter 差し替え

- [推測] `s8b_attempt_registry.py:55-68` の `_FLOOR_CONSUMED_MARKER_KEYS` と `_FLOOR_CONSUMED_MARKER_SCHEMA` は削除する。exact key集合とschemaの正本は admission 側の `_FLOOR_ATTEMPT_KEYS`、`_MEASUREMENT_GENERATION_FLOOR_ATTEMPT_KEYS`、canonical buildersだけにする。`orchestrator/campaign/s8b_holdout_admission.py:4345-4349,4435-4489`
- [推測] `_marker_path()` と raw `_assert_consumed_marker()` を削除する。adapter は `consumed/`、`measurement-generation-consumed/`、marker filename、schema、key集合を一切知らない形にする。`orchestrator/campaign/s8b_attempt_registry.py:1458-1509`
- [推測] `_begin_attempt_observation()` は `consumption_marker` を必須 keywordで受け、classification claimを確認した後、core observation transitionより前に admission-owned private assertionで全 registry identityと照合する。`orchestrator/campaign/s8b_attempt_registry.py:1521-1569`
- [推測] public signatures は次へ変える。

```python
def begin_attempt_observation(
    classified: ClassifiedAttempt,
    *,
    consumption_marker: admission.FloorAttemptConsumptionMarker,
) -> CapturedObservation:
    ...

def begin_classified_failure_observation(
    failure: ClassifiedFailure,
    *,
    consumption_marker: admission.FloorAttemptConsumptionMarker,
) -> CapturedObservation:
    ...
```

- [推測] `resume_attempt()` には `consumption_marker: FloorAttemptConsumptionMarker | None = None` を追加する。start-only/classification-only resumeでは `None` を許すが、durable `observation-start` が存在する枝では matching capabilityを必須にする。capabilityが渡された場合は phaseにかかわらず identityを検査し、unused capabilityとして無視しない。`orchestrator/campaign/s8b_attempt_registry.py:1765-1835,2033-2069`
- [推測] capability不在・型違反・identity不一致では、core observation row追加前に `S8BAttemptRegistryError` へ翻訳して拒否する。registry bytesを部分更新しない。
- [実測] legacy v1 の canonical validator、path dispatch、cut-6 recoveryは admission 側に残る。削除対象は adapter の不完全な重複validatorだけである。`orchestrator/campaign/s8b_holdout_admission.py:4492-4672,4827-4924`
- [実測] launcher は現在 capabilityを渡さず one-argumentの adapter APIを呼ぶ。launcher変更は単位Cなので、B1 checkpointは単独でproduction-callableにはならず、D1341どおり unlandedで保持する必要がある。`orchestrator/campaign/s8b_floor_attempt_launcher.py:533-545,628-645`
- [推測] B1 では launcher に互換fallbackを足さない。raw marker fallbackも残さない。

## B1 — 受理集合

| 入力 | 変更前 | 変更後 |
|---|---|---|
| [実測] exact legacy v1 marker、正しいlegacy claim・主台帳あり | adapterは受理する。admission-issued legacy capabilityを再構築できる入口では引き続き受理する。`orchestrator/campaign/s8b_attempt_registry.py:1458-1509`, `orchestrator/campaign/s8b_holdout_admission.py:4549-4672` |
| [実測] exact legacy v1 markerだけあり、claim・主台帳なし | adapterは現在受理する。変更後は capabilityを発行できず拒否する。これは受理の縮小である。`orchestrator/tests/test_s8b_attempt_registry.py:174-203,918-933` |
| [実測] exact legacy markerと矛盾するclaim・主台帳 | adapterはclaim・主台帳を読まないため現在受理しうる。変更後は完全再導出で拒否する。`orchestrator/campaign/s8b_attempt_registry.py:1463-1509`, `orchestrator/campaign/s8b_holdout_admission.py:4567-4672` |
| [実測] exact current measurement-generation marker、正しいclaim・主台帳あり | adapterはlegacy `consumed/` pathしか見ないため現在拒否する。変更後は admission capability経由で受理する。これは唯一の意図した受理拡大である。`orchestrator/campaign/s8b_attempt_registry.py:1458-1476`, `orchestrator/campaign/s8b_holdout_admission.py:4519-4540,4675-4824` |
| [実測] current markerのextra/missing key、wrong schema/event/role | 現在はcanonical current pathを見ないため結果的に拒否する。変更後もexact current validatorで拒否する。受理拡大はない。`orchestrator/campaign/s8b_holdout_admission.py:4680-4706` |
| [実測] current markerのcampaign/manifest/run/cell/holdout/config/generation/attempt改竄 | 現在は拒否、変更後もclaim・主台帳からの完全再導出で拒否する。`orchestrator/campaign/s8b_holdout_admission.py:4724-4824` |
| [実測] marker symlink、non-regular、非canonical JSON、複数行 | 現在も拒否、変更後も admission canonical readerで拒否する。`orchestrator/campaign/s8b_attempt_registry.py:509-547`, `orchestrator/campaign/s8b_holdout_admission.py:1228-1241` |
| [実測] markerあり、attempt-ledgerなし | 現在受理し、変更後も受理する。cut-6回復可能性を失わない。`orchestrator/tests/test_s8b_attempt_registry.py:918-933`, `orchestrator/campaign/s8b_holdout_admission.py:4827-4924` |
| [推測] 正しいmarkerだが capabilityなし | 変更前は受理、変更後は拒否する。adapterはraw filesystem evidenceを直接権限にしない。 |
| [推測] 別root・別generation・別attemptの valid capability | 変更前はcapability概念がない。変更後はprivate identity照合で拒否する。 |
| [推測] constructorで作った未発行 capability | 変更後は exact typeだけでなく process-local sealも要求して拒否する。 |

- [実測] 受理拡大は「正しい現行 measurement-generation claim・主台帳・markerから admission が発行した capability」だけである。malformed markerや自己申告identityを新たに受理する拡大ではなく、producerが既に書いている現行schemaを正しいvalidatorへ接続する修正である。`orchestrator/campaign/s8b_holdout_admission.py:4238-4271,4435-4489`

## B1 — 既存で直接赤になる test

- [実測] `begin_attempt_observation()` または `begin_classified_failure_observation()` を直接、capabilityなしで呼ぶ次の14 nodeが直接赤になる。`orchestrator/tests/test_s8b_attempt_registry.py:302-1009,1086-1132`

  - `orchestrator/tests/test_s8b_attempt_registry.py::test_handle_registry_rejects_constructor_and_replace_forgery`
  - `...::test_slot_classification_claim_allows_exact_retry_and_rejects_new_reason`
  - `...::test_mut_t1668_obs_after_preout_digests_actual_output`
  - `...::test_failure_observation_without_classification_remains_rejected`
  - `...::test_failure_observation_cannot_be_recorded_twice`
  - `...::test_failure_observation_after_terminal_remains_rejected`
  - `...::test_failure_observation_after_recovery_remains_rejected`
  - `...::test_observe_rejects_classification_claim_identity_tampering`
  - `...::test_observe_rejects_claim_receipt_digest_mismatch`
  - `...::test_observe_rejects_absent_consumed_marker_then_accepts_marker`
  - `...::test_marker_without_attempt_ledger_authorizes_observe`
  - `...::test_observe_rejects_consumed_marker_extra_key`
  - `...::test_observe_requires_exact_consumed_marker_contract`
  - `...::test_resume_classification_and_incomplete_reader_add_no_rows`

- [推測] wrong-handle testsにも valid capabilityを渡し、従来どおり handle forgery/type gateまで到達させる。missing-argument `TypeError` を成功扱いしない。
- [推測] marker tamperの期待方向は維持し、検査所有者だけを admission APIへ移す。extra keyやidentity改竄を「capabilityなし」で代用しない。

## B1 — fixture経由で transitive に赤になる test

- [実測] `_observe()` が raw legacy markerを書いてone-argument APIを呼ぶため、次の7 nodeが transitive に赤になる。`orchestrator/tests/test_s8b_attempt_registry.py:174-203,267-381,1064-1080,1135-1181,1330-1406,1701-1740`

  - `orchestrator/tests/test_s8b_attempt_registry.py::test_terminal_rejects_unclassified_handle_and_accepts_full_order`
  - `...::test_terminal_requires_exact_stored_receipt_and_accepts_restored_bytes`
  - `...::test_terminal_independently_rejects_changed_cached_receipt_bytes`
  - `...::test_relative_repo_root_is_canonicalized_before_handle_is_issued`
  - `...::test_resume_start_and_seal_without_old_handle_reaches_terminal`
  - `...::test_classification_publish_faults_pin_slot_claim_before_exact_retry`
  - `...::test_adapter_preserves_caller_repetition_without_derivation`

- [推測] `_observe()` を「markerを直接書くhelper」から「current admission fixtureでconsumeし、validatorからcapabilityを得て渡すhelper」へ変える。この1箇所で上記7 nodeの契約を更新する。
- [実測] `s8b_floor_evidence_fixture.py` の既存 `build_floor_admission_evidence()` はhistorical v1/v2 bytes専用であり、current digestを学ばないと明記されている。既存helperのbytesは変えない。`orchestrator/tests/s8b_floor_evidence_fixture.py:1-7,192-204`
- [推測] adapter統合test用には同fileへ別名の `issue_current_floor_admission_for_attempt()` を追加し、production reservation/finalize/consumeを使って current token、attempt ID、marker capability、registry identityを返す。既存historical builderの値・戻り型は変えない。

## B1 — 更新・新設 test 計画

| 向き | nodeid |
|---|---|
| [推測] field正例 | `orchestrator/tests/test_s8b_holdout_admission.py::test_cell_admission_projects_current_claim_digest_and_is_frozen` — fresh/resume tokenのfieldがdurable claim digestと一致し、代入が失敗する。 |
| [推測] inspector射影 | `...::test_inspector_reconstruction_projects_current_digest_and_legacy_none` — constructor spyでcurrentはdigest、legacy v1/v2は`None`を確認する。 |
| [推測] API正例 | `...::test_floor_marker_capability_accepts_exact_current_marker` — consume済みcurrent markerからopaque capabilityが返る。 |
| [推測] cut-6正例 | 既存 `test_marker_without_attempt_ledger_authorizes_observe` をcurrent capability化し、attempt ledger欠落のまま通ることを維持する。 |
| [推測] marker不在 | `...::test_floor_marker_capability_rejects_absent_marker` |
| [推測] marker shape | `...::test_floor_marker_capability_rejects_marker_shape_or_schema_tamper` — extra、missing、schema、event、roleをparametrizeする。 |
| [推測] marker identity | `...::test_floor_marker_capability_rejects_marker_identity_tamper` — attempt、campaign、manifest、run、cell、holdout、configuration、cell effect、generation digest、claim digestを分ける。 |
| [推測] claim identity | `...::test_floor_marker_capability_rejects_claim_generation_identity_tamper` — claimと主台帳を同期改竄してもgeneration IDの再導出で拒否する。 |
| [推測] claim coverage | `...::test_floor_marker_capability_rejects_claim_attempt_coverage_tamper` |
| [推測] 主台帳 | `...::test_floor_marker_capability_rejects_missing_duplicate_or_mismatched_main_row` |
| [推測] adapter正例 | `orchestrator/tests/test_s8b_attempt_registry.py::test_observe_accepts_admission_verified_current_marker_capability` |
| [推測] raw fallback拒否 | `...::test_observe_rejects_raw_marker_without_capability` — exact legacy raw markerだけでは進めない。 |
| [推測] forged capability | `...::test_observe_rejects_unissued_marker_capability_before_registry_transition` — observation rowが増えないことも確認する。 |
| [推測] identity移植 | `...::test_observe_rejects_marker_capability_from_other_root_generation_or_attempt` — root、generation、attemptの3方向を分ける。 |
| [推測] classified failure | 既存 `test_mut_t1668_obs_after_preout_digests_actual_output` をcapability付きにし、failure handleにも同じmarker権限が必要なことを固定する。 |
| [推測] resume正例 | 既存 `test_resume_classification_and_incomplete_reader_add_no_rows` のobserved枝へ同じidentityの再検証済みcapabilityを渡す。 |
| [推測] resume負例 | `...::test_resume_observed_phase_requires_matching_marker_capability` — missing、forged、別attemptを分け、reader呼出し前に拒否する。 |
| [推測] signature | `...::test_observation_adapter_requires_keyword_only_marker_capability` —両begin APIのrequired keywordとresumeのoptional fieldを固定する。 |

## B1 — 変異事前登録候補

| ID | 変異と kill test |
|---|---|
| [推測] M1 | `CellHoldoutAdmission` fresh構築で `row["measurement_generation_claim_digest"]` の代わりに `cell_effect_digest` または`None`を渡す。`test_cell_admission_projects_current_claim_digest_and_is_frozen` が落ちる。`orchestrator/campaign/s8b_holdout_admission.py:1793-1811` |
| [推測] M2 | inspector current構築でclaim digestを`None`にする、またはlegacyへcurrent digestを入れる。`test_inspector_reconstruction_projects_current_digest_and_legacy_none` が落ちる。`orchestrator/campaign/s8b_holdout_admission.py:6227-6246` |
| [推測] M3 | validatorのpathを `root / "consumed"` に固定する。`test_floor_marker_capability_accepts_exact_current_marker` が落ちる。`orchestrator/campaign/s8b_holdout_admission.py:4519-4546` |
| [推測] M4 | `_measurement_generation_claim_identity(claim)` の呼出しを削る。claimと主台帳のgeneration IDを同期改竄する `test_floor_marker_capability_rejects_claim_generation_identity_tamper` が落ちる。`orchestrator/campaign/s8b_holdout_admission.py:835-933,4696-4739` |
| [推測] M5 | exactly-one主台帳検査または `main != expected_main` を削る。`test_floor_marker_capability_rejects_missing_duplicate_or_mismatched_main_row` が落ちる。`orchestrator/campaign/s8b_holdout_admission.py:4761-4807` |
| [推測] M6 | canonical markerとのdict完全一致を削り、claim digestとattempt IDだけを見る。`test_floor_marker_capability_rejects_marker_identity_tamper` が落ちる。`orchestrator/campaign/s8b_holdout_admission.py:4808-4824` |
| [推測] M7 | capabilityのexact typeまたはprocess-local seal検査を削る。`test_observe_rejects_unissued_marker_capability_before_registry_transition` が落ちる。 |
| [推測] M8 | adapter capability照合からattempt IDを落とす。same generationの別attempt capabilityを渡す `test_observe_rejects_marker_capability_from_other_root_generation_or_attempt` が落ちる。`orchestrator/campaign/s8b_attempt_registry.py:1521-1545` |
| [推測] M9 | capability identityからrootまたはgeneration claim digestを落とす。cross-rootまたはsame-attempt cross-generation caseが無ければ生きた検査を通り抜ける恐れがあるため、M8のtestに両方向を必ず含める。 |
| [推測] M10 | capabilityなしの場合だけ旧 `_marker_path()` へfallbackする。`test_observe_rejects_raw_marker_without_capability` が落ちる。`orchestrator/campaign/s8b_attempt_registry.py:1458-1509` |
| [推測] M11 | adapter capability assertionをcore observation追加後へ移す。negative testでregistry bytes不変まで見なければ通り抜ける恐れがある。`test_observe_rejects_unissued_marker_capability_before_registry_transition` でbefore/after bytes equalityを要求する。`orchestrator/campaign/s8b_attempt_registry.py:1526-1562` |
| [推測] M12 | observed resume枝でcapability検査を省く。`test_resume_observed_phase_requires_matching_marker_capability` が落ちる。`orchestrator/campaign/s8b_attempt_registry.py:2033-2069` |
| [推測] M13 | dataclass fieldへdefault `None`を付ける。runtime正例だけでは生き残る恐れがあるため、field default欠落と2 constructorの明示keywordをsignature testで固定する。`orchestrator/campaign/s8b_holdout_admission.py:249-259,1793-1801,6229-6235` |

## B1 — 実装順と編集面

1. [推測] `orchestrator/campaign/s8b_holdout_admission.py:47-82,249-259,1793-1819,6227-6253` — field射影、opaque型、public API exportを追加する。
2. [推測] `orchestrator/campaign/s8b_holdout_admission.py:4274-4301,4443-4824` — 既存canonical builders/path/claim-main再導出を通すvalidatorとcapability issuerを追加し、current claim identityの再導出を補強する。
3. [推測] `orchestrator/campaign/s8b_attempt_registry.py:55-68,1458-1593,1765-2071` — 重複schema/pathを削除し、begin/resumeをcapability-onlyへ変更する。
4. [推測] `orchestrator/tests/test_s8b_holdout_admission.py:1825-1890,2001-2167` — field、current marker正負、claim/main tamper、cut-6正例を追加する。
5. [推測] `orchestrator/tests/s8b_floor_evidence_fixture.py:183-351` — historical builderを変えず、current admissionを実発行する別fixtureだけを追加する。
6. [推測] `orchestrator/tests/test_s8b_attempt_registry.py:174-203,267-1009,1086-1185` — direct 14 nodeと `_observe()` transitive 7 nodeをcapability契約へ更新し、adapter正負・resume負例を追加する。
7. [実測] `attempt_registry_core.py`、`s8b_attempt_profile.py`、launcher、contract、stats、freeze、producer bytesはB1で変更しない。

## 総括

- [実測] T-2107 の結論は **(i) 機械導出できる**。pre-probe早期分岐をpolicyに含める必要はあるが、分類を左右する値は既存codeと承認済み `reps`、`session_cv_max="0.10"` から得られ、新しい人間判断は不要である。
- [実測] 親 P1-a は結論として real、P1-b の「閾値をpolicy bytesへ入れると機械導出でなくなる」は refuted である。閾値は既に人間所有で凍結済みであり、現在値の射影とdigest計算は機械的に閉じる。
- [推測] B1 は指定編集面だけで実装可能であり、producer bytesを変えず、current markerだけを新たに正しく受理し、legacy raw markerの不十分な受理を狭められる。
- [実測] ただし adapter API変更後のlauncher配線は単位Cまで未成立なので、B1 は単独landせず unlanded checkpointとして保持する必要がある。