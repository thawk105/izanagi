## 1. A1〜A17 と provisional 裁定の検証

[実測] HEAD と local `main` はともに `97ee3cd3a49ebc62914909012687bccd907ac4ae` だった。以下は実走ではなく、この HEAD に対する静的照合結果である。

| anchor | 判定 | 再確認結果 |
|---|---|---|
| A1 | 正 | [実測] `ident.py:196-235` の preimage は `{spec_content, ccbench_commit, search_tag, search_config, trial}`。genome、trigger wire、origin capability は含まない。 |
| A2 | 不足 | [実測] `model.py:66-84` の `trial` は確かに既存 seam。ただし `autonomous_trial_completeness.py:887-893` が素の `f"{trial_id}-{workload}"` を要求するため、P1 を無修正で入れると origin build completeness が落ちる。 |
| A3 | 正 | [実測] `p3_autonomous_workload_trial.py:749-801` は `trial=f"{trial_id}-{workload}"`、`generation_budget` は `search_config` に置く。 |
| A4 | 正 | [実測] `_prepare_campaign_identity()` は `ident.campaign_id()` を `PreparedCampaignIdentity.campaign_id` にし、`trial_registry.py:4926-4938` が `binding.campaign_id` と exact 一致を要求する。ここは論理 campaign の検査として残す。 |
| A5 | 正 | [実測] `loop.py:161-236` は bound cfg から `campaign_identity` と full SHA-256 の `protocol_digest` を導出し、Pegasus では共有 claim root に claim を作る。 |
| A6 | 過大 | [実測] `campaign_claim.py:348-371` は別 path の claim でも同じ `protocol_digest` の LIVE owner を拒否し、`:383-434` は同じ path を `O_EXCL` で拒否する。[推測] 異なる `trial` は異なる preimage になるが、32-bit の `campaign_id` 短縮 hash や SHA-256 の衝突を論理的に不可能とは言えないため、33 identity と33 protocol digest の相異を plan 作成時に明示検査すべき。 |
| A7 | 正 | [実測] `loop.py:427-463,467-533` は WAL terminal を `done` に seed し、同じ variant を再評価しない。 |
| A8 | 不足、重大 | [実測] `_assert_resume_allowed()` は `p3_s4_loop_trigger_gating.py:475-492`、実際の呼出しは `:1037-1044`。Pegasus は `allow_resume=False` (`env_contract.py:253-261`) なので、第1世代が lock、loop state、WAL、provenance のどれかを残した通常の build runでは、第2世代は同じ layout 上で拒否される。 |
| A9 | 正 | [実測] `_run_one_iteration_resolved()` の genome は `p3_s4_loop_trigger_gating.py:768` の `_BASE` 1個で、行ごとの差は `CoderProposalTriggerGating.wire` から作る binding (`:769-775`)。 |
| A10 | 正 | [実測] `reflux_origin_binding.py:175-193,559-564,609-630` は capability に論理 `campaign_id` を1つだけ持ち、prepared と registry の一致を発行条件にする。 |
| A11 | 正 | [実測] `reflux_formal_consumer.py:682-719` の FC03 は `execution_provenance.campaign_id == trial_binding.campaign_id == capability.campaign_id` を要求する。FC05a は `:731-742` の `build_attempt_id` 相異。 |
| A12 | 正 | [実測] `reflux_result_evidence.py:124-132,551-591` の `execution-provenance/v1` exact key は7個。[実測] production module に同 schema を書く関数はなく、存在する生成物は `orchestrator/tests/reflux_origin_fixture_builder.py:382-393` の test fixture だけ。 |
| A13 | 過大 | [実測] `planned_campaign_run_identity` 自体は topology module と tests 以外で未参照。一方 `reflux_formal_consumer.py:745-772` は同じ `run_plan.members[index]` の ordinal、replicate、wire を読むため、「run plan 全体が未参照」ではない。[実測] `p3_autonomous_workload_trial.py:1439-1588` は完成済み envelope を受け取るだけで、production の `MemberRecoveryMaterial` builder は存在しない。 |
| A14 | 正 | [実測] `campaign_lock.py:275-304` は3つの物理 campaign と ordinal を共有 record へ束縛する先例。ただし今回の論理 campaign と物理 run の二層性を直接実装するものではない。 |
| A15 | anchor 不足 | [実測] `s8b_attempt_registry.py:114-145` は `campaign_run_id` を consumption identity に含める。[実測] 測定世代の決定的導出は別ファイル `s8b_holdout_admission.py:782-802` にある。 |
| A16 | 正 | [実測] `trial_registry.py:4222-4276` は capability 発行時だけ `origin_binding` を追加し、`origin_record.campaign_id == binding.campaign_id` を要求する。 |
| A17 | 正 | [実測] `_run_workload()` は `p3_autonomous_workload_trial.py:3790-3810` で1 layout を作り、`:3850` から同じ cfg/layout の generation loopを回す。manifest は `trial_registry.py:743-773` で `generations == 2` を要求する。 |

### `trial` 全参照の意味分類

| 読み手 | P1との関係 |
|---|---|
| `ident.canonical_preimage()`、campaign lock | [実測] `ident.py:196-235,538-580`。接尾辞付き cfg とその layout/lock が一致すれば正常。物理 identity を分ける本体。 |
| `_campaign_cfg_for_site()` | [実測] `p3_s4_loop_trigger_gating.py:458-472`。`trial` は読まず、Pegasus の `measurement_env` と environment contract だけを bindする。衝突なし。 |
| B4 driver classifier | [実測] `p3_b4_protocol.py:10-22`、`p3_b4_closed_critic.py:722-738`、各 driver の `trial=cfg.trial` 呼出し。suffix は固定 B4 trial 名なら classifier を失敗させるが、8c cfg は `_campaign_for()` が作り、`b4_protocol` marker を持たないため `p3_s4_loop_trigger_gating.py:751-763,1044-1057` の分岐は発火しない。 |
| A-1 non-certifying | [実測] `ident.py:56-73` は `cfg.trial == study_id` を要求する。8c cfg は A-1 schema marker を持たないため発火しない。 |
| completeness | [実測] `autonomous_trial_completeness.py:887-899` が素の trial と単一 `cell.campaign_id` を再導出する。origin-specific projection への変更が必須。 |
| Layer 3 report | [実測] `layer3_report.py:937-945` は `lock_trial == trial_id` または `trial_id + "-"` prefix を許すため suffix 自体は通る。ただし同関数は単一 campaign directory を前提にするため、33 run の集約にはそのまま使えない。 |
| その他の `trial=` | [実測] sweep、guided runner、report label、別 study の固定 cfg 構築が大半で、8c の origin branchから呼ばれない。 |

### P1〜P6 の検証結果

- [推測] P1 は「completeness の origin branch追加」と「短縮 hash衝突時の事前拒否」を条件に採用する。
- [推測] P2、P3、P5 は採用する。ただしP2は production run-plan creator不在を成果物へ明記する。
- [推測] P4 は採用ではなく必須。現行 generation loopでは33 run以前に、Pegasusの第2世代が同 layout reuseで止まる。
- [推測] P6 の却下集合はすべて維持する。

## 2. 解消案の設計

### 2.1 二層 identity

[推測] 完全修飾名を次で固定する。

| 層 | 完全修飾表記 | 定義 |
|---|---|---|
| 論理 campaign | `binding.campaign_id`、`PreparedCampaignIdentity.campaign_id`、`OriginBindingCapability.campaign_id`、`trial_binding.campaign_id`、`execution_provenance.campaign_id` | [推測] 1 registered trialにつき1つ。現行FC03の3項等式を維持する。 |
| 物理 campaign run | `run_plan.members[q].planned_campaign_run_identity`、`execution_provenance.campaign_run_identity`、`report.cells[0].campaign_runs[q].campaign_run_identity` | [推測] `q=0..32` ごとに1つ。裸の `campaign_id` や s8b の `campaign_run_id` と混同しない。 |

[推測] `p3_autonomous_workload_trial.py` に次の origin-only helper を置く。

```python
def _origin_campaign_run_config(
    logical_cfg: CampaignConfig,
    query_ordinal: int,
) -> CampaignConfig:
    # exact int 0..32、logical_cfg.trial は non-empty str 必須
    return dataclasses.replace(
        logical_cfg,
        trial=f"{logical_cfg.trial}-q{query_ordinal:02d}",
    )
```

[推測] 導出式は次で固定する。

```text
cfg_q = replace(
    PreparedCampaignIdentity.campaign,
    trial=f"{PreparedCampaignIdentity.campaign.trial}-q{q:02d}",
)
campaign_run_identity[q] = str(ident.campaign_id(cfg_q))
```

[実測] 元の trial は `_campaign_for():794` の `f"{trial_id}-{workload}"`。[実測] 現行 workload 終端は `ycsb-a`、`ycsb-b`、`ycsb-c`、`rr20`、`rr80` であり、物理値は `-q00`〜`-q32` で終わるため、別 trial の素の値 `f"{trial_id'}-{workload'}"` とは一致しない。

[推測] 次を plan作成前の拒否条件にする。

- `logical_cfg.trial` が空、`None`、exact `str` 以外。
- `query_ordinal` が exact `int` の `0..32` 以外。
- 33個の `campaign_run_identity` が相異でない。
- 33個の `canonical_preimage(cfg_q)` またはその full protocol digest が相異でない。
- run plan内の順序が `q=0..32` と一致しない。

### 2.2 claim、layout、WAL の分離

[実測] `loop.py:194-229` は実際に渡された `cfg_q` から物理 identity、protocol digest、claimを作る。[推測] executorは各qについて必ず次の同一 `cfg_q` を全層へ渡す。

```text
cfg_q
  -> loop._authorize_measurement() の claim
  -> exploration_campaign_layout(campaign_run_identity[q])
  -> campaign.lock / loop_state.json / runs/wal.jsonl / provenance
  -> CampaignSummary.campaign_id
  -> execution_provenance.campaign_run_identity
```

[実測] claim root自体は `env_scope_dir(...)/claims` と共有されるが、`campaign_claim._scan_protocol_conflicts():348-371` は同じ full `protocol_digest` の LIVE ownerだけを拒否する。[推測] 33 preimage/digestと短縮 identityの相異を事前検査した後なら、既に生きている同 processの32 claimは次のclaimと衝突しない。

[実測] `exploration_campaign_layout():589-597` は identity を directory名にする。[推測] layout、WAL、lock、provenance、`done` seedは33個に分離される。

[実測] `_assert_resume_allowed():475-492` は各物理 layoutだけを検査する。[推測] 新executorは各qで `_assert_fresh_campaign_state(layout_q)` を呼び、その後も既存 `_assert_resume_allowed` を通す。どちらも緩和しない。

### 2.3 run plan への束縛

[実測] `TopologyMember.planned_campaign_run_identity` と33値相異検査は `reflux_origin_topology.py:147-182,330-370` に既にある。

[実測] 現在 `build_recovery_envelope()` の production callerはなく、callerは次のtest helperだけである。

- `test_p3_autonomous_workload_trial.py:10278-10321`
- `test_reflux_origin_topology.py:48-79`
- `test_reflux_formal_consumer.py:128-146`

[推測] 実装waveでは `p3_autonomous_workload_trial.py` に新しい `_build_origin_recovery_envelope()` を置き、ここをproductionの唯一の `MemberRecoveryMaterial` creatorにする。入力するmember materialは4要素 `{candidate_salt, result_evidence_salt, constraint_salt, evidence_path}` とし、5番目の `planned_campaign_run_identity` は同関数が `_origin_campaign_run_config()` から計算して足す。外部callerに物理identityを自己申告させない。

[推測] `_prepare_origin_trial_runtime():1518-1571` は同じ33値を独立再導出し、完成した `producer_inputs.run_plan.members[q].planned_campaign_run_identity` と全件exact比較する。1件でも違えば capability発行後、attempt observationおよびorigin ledgerの最初の `BatchReserved` より前に拒否する。

[実測] envelopeは `RecoveryEnvelope` の frozen dataclassで、`write_recovery_envelope_create_only():480-497` がcreate-only write/read-backを行う。[実測] 現行の物理write位置は `_run_workload():3811-3816`。[推測] このwriteを新executorより前、かつorigin ledgerの最初の `BatchReserved` より前に保つ。`trial_registry` のattempt-slot予約は別契約であり、§7.1の `BatchReserved` と混同しない。

### 2.4 証拠側の結線

[推測] `reflux_result_evidence.py:_EXECUTION_PROVENANCE_KEYS` を次の8 keyへ変更する。

```text
schema_version
build_attempt_id
campaign_id
campaign_run_identity
workload
contract_sha256
trigger_binding
execution_receipt_sha256
```

[推測] schema名は `execution-provenance/v1` のまま拡張する。[実測] production producerも受理済み/frozen artifactも存在せず、旧readerを保持すべきhistorical bytesがない。[実測] test fixtureとfixture baselineは証拠artifactではなく、同じ実装変更で更新できる。[推測] この状態でv2とlegacy decoderを新設する方が、発火しない互換面を増やす。

[推測] `reflux_formal_consumer.py:_validate_execution_provenance_bindings()` の引数へ `run_plan` を追加し、FC03で次を合接する。

```text
execution_provenance.campaign_id
  == trial_binding.campaign_id
  == capability.campaign_id

execution_provenance.campaign_run_identity
  == run_plan.members[q].planned_campaign_run_identity
```

[推測] 新 `FormalReasonCode` は作らない。論理/物理campaign identityのbinding違反は既存FC03の責務である。

[推測] consumerは観測した33 `execution_provenance.campaign_run_identity` の相異もFC03内で明示検査する。[実測] これは「planned値との全件一致」と `RecoveryEnvelope.__post_init__()` のplanned相異から論理的には導出可能なので、独立のmutation targetにはしない。

[実測] FC05aの `build_attempt_id` 相異は独立である。異なる物理 campaign identityでも同じattempt IDを再利用でき、逆に異なるattempt IDだけでは33 layout実行を示さないため、FC03の物理identity検査とFC05aはどちらも必要。

### 2.5 producer の最小要件

[推測] 物理evidence issuerは `p3_s4_loop_trigger_gating.py:_run_one_iteration_resolved()` の `run_campaign()` return直後、現行 `:811-829` に置く。outer 8c report builderはissuerにしない。

[実測] native trigger binding WALは `wal.log_trigger_binding():1595-1611` が次のshapeで書く。

```text
stage == "trigger_binding"
payload.build_attempt_id
payload.trigger_binding
```

[実測] 現formal consumerの `_wal_trigger():722-728` はfixture shapeのroot `kind=="TriggerGateBinding"` とroot `trigger_binding` を要求するためproduction shapeを読めない。

[推測] producerはnative WALを別shapeに捏造せず、ordered projectionにnative `{variant, stage, env_tag, ts, payload}` を保存する。consumer側の `_wal_trigger()` を次の条件へ直す。

- exact 1 recordの `stage == trigger_gate_binding.WAL_RECORD_STAGE`。
- `payload.build_attempt_id` が対象attemptと一致。
- `payload.trigger_binding` を `trigger_gate_binding.validate_record()` で検証。
- validated maskから `candidate_wire` を再導出し、binding commitmentを再計算。
- build-startの `trigger_gate_binding_commitment` と一致。

[推測] terminal判定も `_validate_wal_outcomes()` のroot `kind` 固定をnative `stage` とfixture `kind` の閉じたdecoderへ揃える。未知shapeを許す一般fallbackにはしない。

[実測] execution receiptは `CampaignSummary.execution_receipt` (`loop.py:57-82,458-462`) から取得でき、trigger harnessは現在も `p3_s4_loop_trigger_gating.py:821-829` でdigestをprovenanceへ書く。

[推測] `campaign_run_identity` はreceiptだけからは取得できない。producerは次の3項を照合して実値とする。

```text
CampaignSummary.campaign_id
== str(ident.campaign_id(campaign_cfg_q))
== run_plan.members[q].planned_campaign_run_identity
```

[推測] producerはterminal WALとexecution receiptが揃った後、ordered WAL projection、`execution-provenance/v1`、result-evidence recordの順にcreate-only write、fsync、read-backする。1つでも欠ける、actual/planned identityが違う、receiptが `None`、WALが対象attemptへ一意に帰属しない場合はrecordを発行せず、当該q以降をtombstoneにする。

### 2.6 origin topology executor

[推測] `p3_autonomous_workload_trial.py` に次のorigin-only executorを置く。

```python
def _execute_origin_topology(
    *,
    prepared: PreparedCampaignIdentity,
    runtime: OriginTrialRuntime,
    perf: PerfConfig,
    sub: str,
    do_build: bool,
    cache_root: str,
    resolved_site: str,
    contract: env_contract.ExecutionEnvironmentContract,
    build_context: BuildRunContext,
    drive_member: Callable[..., Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    ...
```

[推測] `drive_member` は `(cfg_q, perf, run_plan.members[q], layout_q, ...)` を1回だけ実行するorigin専用adapterとする。productionでは `p3_s4_loop_trigger_gating.py` のtrusted physical harnessだけを渡し、public callerによる任意callback差替えを許さない。

[推測] `_run_workload():3790-3850` は次の排他にする。

```text
origin_runtime is None
    -> 現行 for generation in range(1, generations + 1)

origin_runtime is not None
    -> _execute_origin_topology() の q=0..32
    -> 現行 generation loopへ入らない
```

[推測] origin executorの各qは次を満たさなければ停止する。

- `cfg_q` から再導出したidentityがplanと一致。
- `layout_q == exploration_campaign_layout(campaign_run_identity[q])`。
- `_assert_fresh_campaign_state(layout_q)` が通る。
- `drive_member` の返したactual campaign identityがplanと一致。
- 前qのevidenceがfsync/read-back済みでなければ次qへ進まない。
- source不適用、未証明failure、crash以後はsuffix tombstoneとし、後続を実行しない。

[推測] registered manifestの `generations==2` は論理trial admission metadataとして残すが、origin物理executorの反復数には使わない。これによりPegasusで同一layoutの第2世代を試す経路を避ける。

[推測] origin-bound cellのreport shapeは次に固定する。

```text
campaign_id: <PreparedCampaignIdentity.campaign_id、論理値>

campaign_runs: [
  {
    "query_ordinal": 0..32,
    "campaign_run_identity": <物理値>,
    "campaign_root": <exploration_campaign_layout(物理値).root>
  }
]
```

[推測] `campaign_runs` 各要素はexact 3 key、配列はexact 33件、q昇順、identity/root相異、run planと全件一致を要求する。[推測] origin-bound cellでは意味が一意でない単数 `campaign_root` を出さず、originless cellでは現行 `campaign_root` をそのまま維持する。

[推測] `autonomous_trial_completeness.py` は `launch_admission.origin_binding` の存在を発火条件に、`_check_cell_metadata()`、`_check_cell_campaign_identity()`、`verify_s8c_cross_binding()`、`assert_campaign_layer3_chain()` の単数root処理を33 run検査へ分岐する。未知key一般許可にはしない。

### 2.7 既定経路の不変

| 変更点 | 発火条件と不変条件 |
|---|---|
| cfg suffix | [推測] `origin_runtime is not None` のexecutor内だけ。`_prepare_campaign_identity()` とregistry照合に使う論理cfgは変更しない。 |
| run plan binding | [推測] issued origin capabilityがある場合だけ。originlessではrun plan自体を要求しない。 |
| `execution-provenance` | [推測] origin physical writerだけが生成する。originlessの既存provenance bytesには触れない。 |
| report `campaign_runs` | [推測] `launch_admission.origin_binding` があるcellだけ。originlessではkey自体を出さず、`null`も出さない。 |
| completeness | [推測] origin/non-originのexact key集合を別々にpinする。originlessの受理集合を広げない。 |
| run-start、launch admission、lifecycle | [推測] 新しい物理identityを投影しない。論理 `binding.campaign_id` と既存origin capability recordを維持するため、originless bytesは変わらない。 |

### 2.8 t524 / t1851 との整合

- [実測] t524のslot keyは `trial_registry.py:144-147` の `campaign_id` を含み、 `_reserve_registered_attempt_slot():1387-1395` は `slot["campaign_id"] == binding.campaign_id` を要求する。
- [推測] この `campaign_id` は論理値のままにする。33物理runは1 attempt slotの内側であり、slot、acceptance receipt v5、`prereg_generation` へ物理identityを追加しない。
- [推測] t524の正本surfaceである `trial_registry.py`、`s8c_acceptance_receipt.py` とその専用testsは変更0件。
- [推測] `p3_autonomous_workload_trial.py` はV-8 executorのため変更するが、同ファイルの `_reserve_registered_attempt_slot()` は変更0行。したがってsemantic overlapは0、物理file単位ではt524-adjacentな1件である。
- [推測] t1851の `s8b_attempt_registry.py`、`s8b_holdout_admission.py`、`campaign_run_id`、measurement generationは変更0件。

## 3. 却下案と恒真化監査

### 却下案

| 案 | 判定 |
|---|---|
| P6: claim release / per-attempt key | [推測] 却下。one-shot claimを弱め、crash後の二重実行を許す。 |
| P6: trigger wireをcampaign identityへ入れる | [推測] 却下。sourceと同mask validationの科学上必要な再実行をwire identityでは区別できない。 |
| P6: `generations=33` | [推測] 却下。manifestのexact 2と意味が違い、Pegasus resume拒否も解かない。 |
| P6: 時刻、PID、乱数identity | [推測] 却下。run plan時点で再導出できずresumeと事前登録を壊す。 |
| (a) capabilityへ33 identityを足す | [推測] 却下。論理launch capabilityと物理planを二重管理し、t524 slotの1 campaign原則と衝突する。 |
| (b) 33 capabilityを発行 | [推測] 却下。1 trial、1 origin、1 attempt slotを33論理campaignへ分裂させる。 |
| (c) FC03のprovenance campaign_idを物理値に置換 | [推測] 却下。既存3項等式を破壊し、別trialのrecord流用防壁を失う。物理値は新keyへ足す。 |
| (d) `search_config["origin_query_ordinal"]` | [推測] 却下。identityは分かれるが、8c search_config exact集合とproducer semanticsを33通り変更する。用途どおりの既存 `trial` seamより変更面が広い。 |
| (e) trial単位claim 1つで同process 33 run | [実測] 現行claimは再取得時に同pathの `O_EXCL` で止まり、1回の `run_campaign` へ33件を入れると`done`で重複skipする。[推測] 成立させるには既存防壁の迂回が必要なので却下。 |
| (f) planned identityを検査せずlayout存在だけ確認 | [推測] 却下。実行後に都合のよい33 directoryをplanへ対応付けられ、事前登録が恒真になる。 |

### 提案検査の恒真化監査

| 検査 | 偽装すると素通りするもの |
|---|---|
| 論理cfgから33 planned identityを再導出 | [推測] logical cfgとrun planを同時に偽装すれば通るため、先にissued bindingと`PreparedCampaignIdentity.campaign_id`を照合する必要がある。 |
| planned 33値の相異 | [推測] 33個の偽identityを並べるだけで通るため、実行後の`CampaignSummary.campaign_id`と結ぶ必要がある。 |
| actual identity == planned identity | [推測] harnessがactual値をplanからコピーする実装なら恒真になるため、`CampaignSummary.campaign_id`とbound cfgから独立取得する。 |
| execution provenance 33値相異 | [推測] 物理実行0件でも33文字列を捏造すれば通るため、WAL、receipt、actual layoutとの束縛を合接する。 |
| FC03論理3項等式 | [推測] 3値を同じ偽値に揃えれば通るため、issued capabilityとregistry bindingのseal/rederivationを残す。 |
| native WAL trigger binding一致 | [推測] WALとrecordを同じwriterが同時偽造すれば通る。§3.6のtrusted harness運用前提より強い主張はしない。 |
| execution receipt digest | [推測] digestだけを自己申告すれば通るため、`CampaignSummary.execution_receipt` のcanonical bytesからharness内で計算する。 |
| report `campaign_runs` とrun plan一致 | [推測] reportとplanの双方を偽装すれば通るため、各campaign.lock、WAL、provenanceも再読する。 |
| origin-only発火条件 | [推測] JSONへ偽の `origin_binding` を足すだけで通さず、runtimeではissued capability object、offlineではexact launch bindingとの一致を要求する。 |

## 4. 裁定パッケージ候補と実装wave受入要件

### 残る択一

[推測] 残る設計択一は0件。以下を本案で固定した。

- `execution-provenance/v1` をin-place拡張し、v2は作らない。
- 物理identity違反は新reasonではなくFC03。
- origin reportは論理 `campaign_id` とexact 33件の `campaign_runs` を持ち、単数 `campaign_root` は持たない。
- run-plan builderとexecutorは `p3_autonomous_workload_trial.py`、物理evidence finalizerはtrusted harnessの `p3_s4_loop_trigger_gating.py` に置く。

### 実装waveへの受入要件と変異事前登録候補

| # | 受入要件 | 変異位置、無効化する述語、期待する赤 |
|---|---|---|
| 1 | [推測] q00〜q32のcfgとidentityを決定的に導出し、33値を相異にする。 | `p3_autonomous_workload_trial.py:_origin_campaign_run_config`。qを固定0へ変異。run-plan construction testがduplicate identityで赤。 |
| 2 | [推測] supplied envelopeのplanned identityを論理cfgから独立再導出する。 | 同 `_prepare_origin_trial_runtime`。plan照合を無効化し、q17だけ別identityにしたpreflight負例が赤。後段まで進めない単一理由testにする。 |
| 3 | [推測] origin executorはgeneration loopと排他で、33 layout各々へfresh checkを掛ける。 | 同 `_execute_origin_topology`。全qでq0 layoutを再利用する変異。q1のlayout/identity不一致またはfresh-state負例が赤。 |
| 4 | [推測] `execution-provenance/v1` は `campaign_run_identity` を必須exact keyとしてparseする。 | `reflux_result_evidence.py:_EXECUTION_PROVENANCE_KEYS/_validate_execution_provenance`。key必須を外す変異。欠落provenanceが受理される負例が赤。 |
| 5 | [推測] provenance物理identityを同ordinalのplanned identityへ束縛する。 | `reflux_formal_consumer.py:_validate_execution_provenance_bindings`。比較を無効化。33値は相異のまま1つ循環shiftした負例がFC03にならず赤。 |
| 6 | [推測] `build_attempt_id` の相異をFC05aで独立維持する。 | 同 `_validate_bijection`。set比較を無効化。campaign run identityは33個正しいがattempt IDを1件重複させた負例が赤。 |
| 7 | [推測] production native WALの `stage/payload` shapeを検証し、fixture-only shapeへ依存しない。 | 同 `_wal_trigger` と `_validate_wal_outcomes`。native decoderを無効化。`wal.log_trigger_binding()` 相当の正例がFC05c/FC07で赤。 |
| 8 | [推測] producerはplanned値のコピーでなくactual `CampaignSummary.campaign_id` を使う。 | `p3_s4_loop_trigger_gating.py:_finalize_origin_member_evidence` 新設部。actual/planned比較を無効化。summaryだけ別identityにした負例がrecordを書いてしまい赤。 |
| 9 | [推測] origin reportの `campaign_runs` をexact 33件で再検査し、originless bytesを変えない。 | `autonomous_trial_completeness.py` のorigin projection branch。q配列のexact照合を無効化し、q8/q9を入替えた負例が赤。加えてorigin branchを常時発火へ変異すると既存originless projection比較が赤。 |

[推測] 単独の「provenance 33値相異」変異は登録しない。planned全件一致とplan側相異が生きている限り同じ入力を先に拒否し、単一理由のkillにならないためである。

### 実装waveが触れる予定のfile

[推測] docsと記録を除く最小予定は12 file。

1. `orchestrator/campaign/p3_autonomous_workload_trial.py`
2. `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
3. `orchestrator/campaign/reflux_result_evidence.py`
4. `orchestrator/campaign/reflux_formal_consumer.py`
5. `orchestrator/campaign/autonomous_trial_completeness.py`
6. `orchestrator/tests/test_p3_autonomous_workload_trial.py`
7. `orchestrator/tests/test_p3_s4_loop_trigger_gating.py`
8. `orchestrator/tests/test_reflux_result_evidence.py`
9. `orchestrator/tests/test_reflux_formal_consumer.py`
10. `orchestrator/tests/test_autonomous_trial_completeness.py`
11. `orchestrator/tests/reflux_origin_fixture_builder.py`
12. `orchestrator/tests/reflux_origin_fixture_baseline.json`

[推測] `reflux_origin_topology.py` は既にplanned identity field、33件exact、相異検査を持つため変更不要。`trial_registry.py`、`s8c_acceptance_receipt.py`、全 `s8b_*` は変更不要。

## 総括

- [推測] P1: 条件付き採用。completeness分岐とhash衝突時拒否を追加する。
- [推測] P2: 採用。物理identityの正本はrun plan。
- [推測] P3: 採用。logical `campaign_id` を残し、physical keyを追加する。
- [推測] P4: 採用かつ必須。Pegasusの同layout第2世代は現行経路で通らない。
- [推測] P5: 採用。t524 attempt slotの `campaign_id` は論理値のまま。
- [推測] P6: 全案を却下。
- [推測] 残る択一は0件。
- [推測] 実装waveの予定変更file数は12件。
- [実測] 本回答では実装、docs編集、commit、pytest実走を行っていない。