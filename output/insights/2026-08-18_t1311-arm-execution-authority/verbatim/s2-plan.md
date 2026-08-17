## 総括

実装方針は、manifest の `arm` 文字列を照合するのではなく、`arm` が選択した実 descriptor の canonical bytes を封印し、その SHA-256 を全 6 sink へ通す構成とする。`report["executed_arm"] == binding.arm` 型の恒真検査は一切導入しない。

現 HEAD `2a3b5055` には T-1310 の正式 workload profile resolver がまだ存在しないため、実装順は必ず `T-1310 → 単位 A → 単位 B → 検証単位 C` とする。resolver が無い状態では正式 launch を拒否し、推測値や既存 pilot 定数へ fallback しない。

この段では read-only の静的調査だけを行った。書込み、pytest、build は実行しておらず、worktree は clean である。

### 1. `off` の canonical input

新設物は次の 4 点とする。

|場所|内容|
|---|---|
|`orchestrator/campaign/s8c_arm_inputs.py:1`|厳密 canonicalizer、T-1310 profile adapter、中立入力生成器・検証器・resolver|
|`orchestrator/campaign/s8c_arm_input_freeze_schema.v1.json:1`|freeze sidecar の独自 schema|
|`output/s8c-preregistration/arm-inputs/off-neutral-descriptor.v1.json:1`|role へ実際に渡す descriptor bytes|
|`output/s8c-preregistration/arm-inputs/freeze.v1.json:1`|path、hash、導出規則、元 profile hash を固定する sidecar|

`off-neutral-descriptor.v1.json` 自体は既存の `orchestrator/campaign/s8b_descriptor_schema.json:1-38` に従い、`on` / `swapped` と完全に同じ 7 top-level field と同じ nested field 集合を持たせる。独自の `schema_version` は wrapper である `freeze.v1.json` の `s8c-arm-input-freeze/v1` に置く。これにより、「実入力は `8b-v1` と同型」と「新規 freeze は独自 version」の双方を満たす。

生成規則は、T-1310 が提供する H1/H2 正式 profile を結果非依存に使う。

- `read_ratio_percent` は凍結済み端点 80 と 20 の算術中点 50。端点の順序に依存せず、両端から等距離であるため恣意的な第三値ではない。和が奇数なら丸めず生成拒否する。
- `rmw`、`contention`、`scale`、`objective`、`correctness` は H1/H2 の完全一致を要求して、その共通値を複製する。一致しなければ一方を選ばず拒否する。
- `source` は、実 benchmark projection ではなく中立値を明示生成するため `human_declared`。
- 全 workload が同一の一ファイルを読む。workload ごとの `off` 生成物は作らない。

T-1310 の予定値が H1/H2=`80/20, rmw=0, skew=0.9, records=1,000,000, threads=48` のままなら、改行なしの canonical bytes は次の 262 bytesとなる。

`{"contention":{"label":"high","skew":0.9},"correctness":"serializable_legacy_and_s2","objective":"maximize_throughput_tps","read_write":{"read_ratio_percent":50,"rmw":0},"scale":{"records":1000000,"threads":48},"schema_version":"8b-v1","source":"human_declared"}`

その SHA-256 は `b2c6a26304c78dadc62b4bc8996b4876e0ad6f1faba6eafd16e2b372f62208c3`。T-1310 の正式値がこれと異なる場合は、この literal を都合よく変更せず generator を失敗させ、profile 側との不一致を先に裁定する。

新設 API は以下とする。

- `canonical_execution_input_bytes(descriptor: Mapping[str, Any]) -> bytes`
- `derive_off_neutral_descriptor(*, formal_descriptors: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]`
- `generate_off_neutral_artifacts(*, repository_root: Path) -> None`
- `verify_off_neutral_artifacts(*, repository_root: Path, commit: str) -> VerifiedOffNeutralInput`
- `resolve_arm_input(*, arm: str, holdout: str, repository_root: Path, commit: str) -> ResolvedArmInput`

検証器は UTF-8、duplicate key、BOM、非有限数、未知 field、symlink、非通常ファイル、余分な空白、末尾 LF を拒否する。`json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)` の再生成 bytes と完全一致させる。正式 launch では working-tree path を直接信じず、`binding.measurement_head` の commit blobを読み、その bytes を封印後は再読込しない。

`off` ファイルを読む production 関数は `trial_registry.bind_trial_arm` だけとし、p3 runner が path を直接読む経路は作らない。受入時も同じ verifier を historical `measurement_head` に対して再実行する。

### 2. sealed execution digest

定義は次の一式に限定する。

`sealed_execution_digest_sha256 = SHA256(canonical_execution_input_bytes(selected_descriptor))`

hash preimage に含めるのは、role へ渡す descriptor 本体の canonical bytes だけである。arm 名、trial ID、holdout 名、sidecar、path、campaign ID は含めない。

arm 名を混ぜると、同じ入力 bytes に異なる label を付けただけで別 digest になり、「digest が違えば実入力が違う」が崩れる。bytes-only なら、resolver が誤って `on` と `swapped` に同じ入力を返した場合も同一 digest となり、別入力を装えない。

label 交換は次の経路で検出する。

1. manifest の `arm` が別 label へ交換される。
2. `bind_trial_arm` がその label に従って別の実 descriptor bytes を解決する。
3. bytes-only digest が変わる。
4. digest を含む `CampaignConfig.search_config` から再導出した campaign ID が manifest pin と一致せず、`assert_campaign_binding` が拒否する。
5. 仮に campaign pin まで変更されても、run-start、cell descriptor、proposal、invocation、terminal report の digest chain と historical resolver の再導出を受入側が検査する。

同時に、「同一 bytes を label だけ変更しても digest は同一」という独立テストを置く。これが、label の自己申告を authority にしていない証拠になる。

### 3. `bind_trial_arm` と resolver

`orchestrator/campaign/trial_registry.py:69-70` の既存 seal 群に `_TRIAL_ARM_EXECUTION_SEAL` を追加し、`TrialBinding` の直後、現在の `:153-166` 付近に次を置く。

`TrialArmExecutionBinding` は少なくとも、元の exact `TrialBinding` オブジェクト、module-issued `ResolvedArmInput`、canonical bytes、`sealed_execution_digest_sha256`、private seal を保持する。

entrypoint は、`assert_issued_trial_binding` の直後、現在の `:1191-1199` に配置する。

`def bind_trial_arm(binding: TrialBinding, *, repository_root: Path) -> TrialArmExecutionBinding`

resolver callback を引数にしない。production resolver を caller が差し替えられる API にすると authority が caller 側へ戻るためである。

dispatch は `ARMS` (`trial_registry.py:49`) を唯一の closed set とする。

- `on`: `binding.holdout` の T-1310 正式 profileを解決する。
- `off`: historical commit にある中立 descriptor と freeze sidecar を検証して読む。
- `swapped`: `HOLDOUTS` (`:50`) から自分以外を列挙し、件数が厳密に 1 であることを要求して、その holdout を T-1310 resolver へ渡す。新しい derangement table は作らない。
- `HOLDOUT_BINDINGS` (`:51-54`) は対象 workload と rratio の整合確認に使うが、欠けている skew/rmw/scale を補う情報源にはしない。

T-1310 resolver が未実装、対象 holdout 不在、flags 不完全、descriptor 不正、期待 rratio 不一致のいずれでも `[arm-input-resolution]` で launch admission 中に拒否する。`on` への fallback、`{}` descriptor、pilot の `100k/4`、`s8b_holdout_freeze.HOLDOUTS` の production 代用は禁止する。

関係する既存関数は次のように変える。

- `admit_registered_launch` (`trial_registry.py:1318-1368`) が `load_launch_binding` の直後に `bind_trial_arm` を一度呼び、`TrialLaunchAdmission.arm_execution` に格納する。
- `admit_unregistered_exploratory` (`:1252-1315`) は `arm_execution=None` のまま。
- `assert_issued_trial_launch_admission` (`:1371-1412`) は registered admission に issued arm execution があり、その内部 `TrialBinding` が `admission.binding` と同一オブジェクトであることを要求する。
- `launch_admission_record` (`:1415-1462`) は registered のみ exact `arm_execution` recordを追加する。exploratory の現行 7-key bytes は変えない。
- `assert_rederived_launch_admission` (`:1465-1503`) は fresh derivation で実入力 bytes と digest まで再照合する。
- `assert_campaign_binding` (`:1894-1903`) の署名を `def assert_campaign_binding(binding: TrialBinding, *, arm_execution: TrialArmExecutionBinding, actual_campaign_id: str) -> None` とし、両 seal、binding object identity、manifest campaign ID を検査する。`binding.arm` と report の文字列比較は置かない。
- `reflux_origin_binding.LaunchAdmissionRederivation` (`reflux_origin_binding.py:145-156,201-270`) に同じ issued arm execution を保持させ、origin 経路で authority を落とさない。

### 4. 6 sink の具体的改修

|sink|現在の呼出し連鎖|改修|
|---|---|---|
|descriptor|`p3_autonomous_workload_trial.py:698-728` → `:2466-2478` → `_common_payload` `:1589-1606`|正式 run では `_prepare_campaign_identity` が `admission.arm_execution` の canonical bytes を decode・再検証し、`WORKLOADS[workload]` から descriptor を作らない。`descriptor_binding` に `sealed_execution_digest_sha256` を追加し、`output_sha256` と完全一致させる。`workload_flags` と `_perf_for(flags)` は対象 holdout のままにする。これは `swapped` が benchmark 設定を変えず descriptor だけを交換するという規範に必要。|
|campaign identity|`_campaign_for` `:637-674` → `_prepare_campaign_identity` `:710-727` → `ident.campaign_id`|`search_config` に full `sealed_execution_digest_sha256` と監査用 `arm` を追加する。digest prefixだけは authority に使わない。`spec_slug` と `trial` の既存情報だけに依存しない。正式 preflight の3経路 `:788`, `:871`, `:2467` は同一 arm execution objectを渡す。|
|proposal bytes/path|proposal `:2741-2753`、raw/provider artifact `:1518,:1537`|path を `proposals/arm-{arm}.exec-{64hex}.{workload}.g{generation}.json` とし、proposal canonical bytesにも `arm` と `sealed_execution_digest_sha256` を入れる。write 後に generation recordへ `{path, sha256, sealed_execution_digest_sha256}` を保存し、受入側が実 bytesを再読込できるようにする。|
|invocation namespace|critic `:1963-1969`、planner/coder/auditor `:2613-2726`、namespace `:3039-3045`|新 helper `_invocation_id(*, arm, digest, workload, generation, role)` を作り、`arm-{arm}.exec-{full_digest}.{workload}.g{n}.{role}` を全5箇所で使う。最大長は現行 provider の 128 文字制約内。既存 `run_root` marker に加え、正式 run は `run_root/invocations/arm-{arm}.exec-{digest}` にも `ensure_exploration_namespace` を適用する。raw、payload、envelope の filename は invocation ID 経由で同 digest を消費する。|
|run-start|`run_trial` の dict `:3078-3104`|report top-level の既存 `arm` 不在契約を反転せず、exact nested record `arm_execution={arm,input_schema_version,sealed_execution_digest_sha256}` を追加する。`launch_admission.arm_execution` と同一 record にする。schema は run-start v4へ進める。|
|terminal report|`_complete_origin_runtime` `:938-972`、report `:2296-2349`|report に run-start と同じ nested `arm_execution` を置き、各 cell の descriptor/campaign/proposal chainから digestを再計算する。`OriginProducerInputs.enforcement_arm` (`:331-340`) は削除し、`:851-857` の caller token検査も削除する。`:962` は issued arm execution digest を既存 `evaluate_formal_origin(enforcement_arm=...)` へ渡す。`reflux_formal_consumer.py:893-923,938-1001,384` の standalone API/schema は変えない。|

`p3_autonomous_workload_trial.py:2413-2450` の active run scope に arm execution capability を保持し、registered run で欠落した場合は `_descriptor_for` へ fallback せず拒否する。pre-manifest campaign ID生成だけは `s8c_arm_inputs.resolve_arm_input` が返した module-issued `ResolvedArmInput` を使用する。

### 5. 完全性検査と受入

`autonomous_trial_completeness.py:1114-1285` の run envelope 検査の直後に、次の検査を新設する。

`def assert_execution_digest_chain(*, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]], attempt_journal: Path, cells: Sequence[Mapping[str, Any]]) -> None`

`assert_autonomous_trial_completeness` の cell decode 後、現在の `:1987-1992` から必ず呼ぶ。

禁止するものは以下。

- registered run の `arm_execution` 欠落、未知 key、非 SHA-256。
- `SHA256(canonical(cell.descriptor))` と sealed digest の不一致。
- `descriptor_binding.output_sha256`、campaign identity、proposal bytes/path、全 invocation ID、run-start、terminal reportのいずれか一つでも digest が欠落または不一致。
- proposal path が run root 外、symlink、非通常ファイル、非 canonical JSON、記録 hash 不一致。
- arm labelだけ一致し descriptor bytes が不一致の run。
- `on` / `swapped` resolver が同じ holdoutを返すこと、または `off` bytes が workload ごとに変わること。

正例は H1/on の正式 descriptor digestが `80501db0235d88314edd4a4c29a1949e67acc2b466ae426fbbb1cb3da4b7d843` となり、campaign search config、`arm-on.exec-8050...rr80.g1.planner`、proposal bytes/path、run-start、report がすべて full digestを持つ一件である。T-1310 の profile bytesが予定値と異なる場合、この literal正例は更新せず profile不一致として停止する。

`autonomous_trial_completeness.py:2291-2342` は、`producer.WORKLOADS[workload]` から期待 descriptorを再生成する現行処理を廃止する。cell の canonical descriptor hashを検証し、その descriptorと sealed digestを `_campaign_for` に再投入して campaign IDを導出する。benchmark `workload_flags` は引き続き対象 workloadと照合する。

`assert_trial_registry_acceptance` (`trial_registry.py:2408-2723`) は名称を維持し、historical `measurement_head` から arm inputを再解決して、run-start/report/cell bytesと比較する。ただし receipt本体は変更しない。`s8c_acceptance_receipt.py:23-28,2688-2711` の v1、`certifying=false`、`c02-arm-binding-unproven` と `t468-approval-authority-absent` をそのまま保持する。`accept_trial` は新設も改名もしないため、凍結契約上の C02 は引き続き `EVIDENCE_UNDEFINED` と報告する。

### 6. caller 棚卸し

現 tree を `rg` で棚卸しした結果は以下。行番号は変更前 HEAD 基準である。

- `_campaign_for` の production caller は `p3_autonomous_workload_trial.py:710` と `autonomous_trial_completeness.py:2330`。test caller は `test_p3_autonomous_workload_trial.py:340,359,5356`、`test_autonomous_trial_completeness.py:225`、`test_layer3_report.py:1153`。`output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py:29` は既に現 signature の `contract` を欠く historical captured driverなので編集しない。`test_s8c_preregistration_predicates.py:397-409` は同名の局所 fakeで production callerではない。
- `_descriptor_for` の production caller は `p3_autonomous_workload_trial.py:709` と `autonomous_trial_completeness.py:2292`。test caller は `test_p3_autonomous_workload_trial.py:339,357,5355,6377`、`test_autonomous_trial_completeness.py:224`、`test_layer3_report.py:1148`。historical driverは同 `smoke_driver.py:28`。signature は維持し、返す binding に digestを追加する。
- `_prepare_campaign_identity` の production caller は `p3_autonomous_workload_trial.py:788,871,2467`。test caller は `test_p3_autonomous_workload_trial.py:387,5222,5366,5401,6075`。同 test の `:439-457,5733` は wrapper/monkeypatch seamである。
- `assert_campaign_binding` の caller は `p3_autonomous_workload_trial.py:796-799` と `test_trial_registry.py:2551` の2件。
- `admit_registered_launch` の直接 caller は `p3_autonomous_workload_trial.py:752`、`trial_registry.py:1490`、`test_p3_autonomous_workload_trial.py:5292`、`test_reflux_origin_binding.py:332`、`test_trial_registry.py:1392,1597,1627,1675,2008,2044`。
- `launch_admission_record` の caller は p3 `:912,932-934,2977-2978`、registry `:1498-1501,1720`、`test_claude_transport.py:1366`、`test_trial_registry.py:1448,1482-1487,1528,1549,1826,1889`。signature は維持し、registered recordだけが `arm_execution` を持つ。
- `assert_rederived_launch_admission` は p3 `:2075`、`reflux_origin_binding.py:216`、registry `:1704`、`test_trial_registry.py:1517`。`rederive_launch_admission` は p3 `:859`、`reflux_origin_binding.py:504` と `test_reflux_origin_binding.py:349,412,424,459,579`。
- `OriginProducerInputs` の repository 内 constructor は `test_p3_autonomous_workload_trial.py:6490` の1件だけ。ここから `enforcement_arm` (`:6499`) を除く。`test_reflux_formal_consumer.py:187,688` と `test_reflux_origin_client.py:143,482` は standalone formal consumer契約なので期待値を変えない。
- `run_trial`、`_run_workload`、`_finish_trial`、`_invoke` の public/private signatureは変えない。多数の exploratory、transport、session-isolation callerへ arm capability引数を追加しない。authority は sealed admission と active run scope経由で供給する。

### 7. 既存テストの扱い

特に指定された箇所は次のように扱う。

- `test_p3_autonomous_workload_trial.py:51-76,355-374` の過去 campaign ID pinは残す。digest追加後の current値は新しい T-1311 epochとして追加し、過去値を上書き・削除しない。
- 同 `:5192-5236` の6-cell fixtureは、manifest生成前に各 armの `ResolvedArmInput` を解決して campaign IDを作る。全 armを `_prepare_campaign_identity` の既定 on経路へ流さない。
- 同 `:5417-5429` の既存 `assert "arm" not in report` と `assert "holdout" not in report` はそのまま残す。新 authority は nested `arm_execution` と実 descriptor digestで検査し、既存期待を反転しない。
- 同 `:6375-6470` の origin authority descriptorは `_descriptor_for(WORKLOADS["rr80"])` ではなく、issued H1/on canonical bytesから作る。`:6499` の caller指定 `enforcement_arm` は削除する。
- `test_autonomous_trial_completeness.py:92-219` は pre-T343、T343、T428、T530 の historical pinを保持し、T-1311 current epochを追加する。`:2178-2205` の独立 `CampaignConfig` goldenに sealed digestを literalで追加し、`:2363-2368` の current/historical区別を維持する。
- 同 `:409` と `test_trial_registry.py:266` の synthetic formal invocation ID builderは armと full digestを引数に取る。exploratory fixtureの旧 IDを一括で緩めない。
- `test_artifact_admission.py:216-223` の `p3-t178` pathは historical evidence pinなので変更しない。
- `test_reflux_originless_compatibility.py:231-263,581-627` の `_PRE_WAVE_ORIGINLESS_BASELINE` は削除しない。T-1311後の exact baselineと、旧 baselineから許される差分のclosed whitelistを追加する。digest、descriptor、invocation、payload hashを volatile/main-derived扱いへ入れて隠すことは禁止し、各 armの独立 literalへ照合してから旧 baselineへ投影する。
- `test_layer3_report.py:1011-1013,1148-1162` の fake producerと直接 callerは digest付き descriptor/campaign signatureへ更新する。
- `test_claude_transport.py`、`test_role_session_isolation.py` の直接 `provider.invoke(invocation_id=...)` は provider単体検査であり変更しない。
- 6 sinkごとに一つだけ digest消費を除く変異を作り、対応する検査が単独理由で殺す。加えて、旧コード形の arm非依存 campaign、`rr80.g1.planner`、caller由来 `enforcement_arm` を明示変異として置く。

### 8. 素集合の実装単位

1. 単位 A、T-1310後に直列開始

   所有ファイルは `s8c_arm_inputs.py`、新 schema、`output/s8c-preregistration/arm-inputs/` の2 artifact、`trial_registry.py`、`reflux_origin_binding.py`、新 `test_s8c_arm_inputs.py`、`test_trial_registry.py`、`test_reflux_origin_binding.py`。中立入力、digest、seal、`bind_trial_arm`、launch record、historical再導出までを完成させる。

2. 単位 B、Aに依存

   所有ファイルは `p3_autonomous_workload_trial.py`、必要なら `s8c_generation_projection.py`、`test_p3_autonomous_workload_trial.py`、対応 projection test、`test_reflux_originless_compatibility.py`。6 sinkへの実配線と origin caller token除去を行う。

3. 検証単位 C、AとBに依存

   所有ファイルは `autonomous_trial_completeness.py`、`test_autonomous_trial_completeness.py`、`test_layer3_report.py`。digest-chain検査、proposal再読込、Layer-3 campaign再導出、6 sink変異を所有する。

3単位の編集ファイルは重ならない。`docs/` は全単位から除外し、親の所有とする。また、`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`、`output/s8c-preregistration/condition-freeze/`、`s8c_acceptance_receipt.py` は編集対象外である。