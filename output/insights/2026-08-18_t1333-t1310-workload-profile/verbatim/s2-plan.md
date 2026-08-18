# 段 2 実装プラン

結論は、親の P1 が正しいです。`WORKLOADS` の entry を構造化しても、既存コードが identity に投入しているのは flat な YCSB flags と scale の射影です。したがって `cells[].workload_flags` には `entry["ycsb"]` だけを載せれば、探索 workload の bytes と campaign identity を完全に保存できます。台帳の予測は、構造化 entry 全体を現在の `workload_flags` として渡した場合にだけ成立します。

以下は静的検査だけに基づくプランです。pytest は実行しておらず、緑とは報告しません。

## 1. workload entry の型と単一導出経路

`orchestrator/campaign/p3_autonomous_workload_trial.py:191-195` を、概ね次の型へ置き換えます。

```python
class WorkloadEntry(TypedDict):
    ycsb: Mapping[str, str]
    records: int
    threads: int
    pilot_scope: str
    profile_selector: str
    campaign_spec_content: str
    candidate_id: NotRequired[str]


class WorkloadProfileRecord(TypedDict):
    schema_version: str
    selector: str
    source: str
    loader: str
    path: str
    sha256: str
```

探索 entry は現在の値をそのまま構造化します。

```python
EXPLORATORY_PROFILE = "exploratory-ycsb-abc"
FORMAL_LEGACY_PROFILE = "formal-holdout-legacy-v1"

DEFAULT_WORKLOADS = ("ycsb-a", "ycsb-b", "ycsb-c")

WORKLOADS: dict[str, WorkloadEntry] = {
    "ycsb-a": {
        "ycsb": {
            "ycsb_zipf_skew": "0.9",
            "ycsb_rratio": "50",
            "ycsb_rmw": "0",
        },
        "records": 100_000,
        "threads": 4,
        "pilot_scope": EXPLORATORY_PROFILE,
        "profile_selector": EXPLORATORY_PROFILE,
        "campaign_spec_content": CURRENT_EXPLORATORY_SPEC_CONTENT,
    },
    # ycsb-b / ycsb-c も同形
}
```

正式 entry は producer 内に正式比率を書かず、`s8b_holdout_freeze.HOLDOUTS:98-101` を走査して追加します。

```python
for name, authority in s8b_holdout_freeze.HOLDOUTS.items():
    WORKLOADS[name] = {
        "candidate_id": authority["candidate_id"],
        "ycsb": authority["ycsb"],       # copy せず同一 object
        "records": authority["records"],
        "threads": authority["threads"],
        "pilot_scope": FORMAL_LEGACY_PROFILE,
        "profile_selector": FORMAL_LEGACY_PROFILE,
        "campaign_spec_content": FORMAL_NON_CERTIFYING_SPEC_CONTENT,
    }
```

これなら producer file に正式 `ycsb_rratio` 値は現れません。加えて `records` / `threads` も module 表から entry へ入るため、三つ目の scale authority を作りません。

### 三つの sink

現在の引数 `workload_flags` を `entry: WorkloadEntry` に置き換えます。

| 現在位置 | 変更 |
|---|---|
| `p3_autonomous_workload_trial.py:641-688` `_campaign_for` | `entry["ycsb"]`、`entry["records"]`、`entry["threads"]`、`entry["pilot_scope"]` を `search_config` へ射影 |
| `p3_autonomous_workload_trial.py:691-698` `_perf_for` | 同じ entry から `PerfConfig.records`、`threads`、`workload` を構築 |
| `p3_autonomous_workload_trial.py:701-709` `_descriptor_for` | 同じ entry から `projected_input` を構築 |
| `p3_autonomous_workload_trial.py:848-870` | `flags = WORKLOADS[workload]` を `entry = WORKLOADS[workload]` にし、三 sink へ同じ object を渡す |
| `p3_autonomous_workload_trial.py:902-915` | manifest identity も同じ entry を渡す |
| `p3_autonomous_workload_trial.py:2816-2856` | cell は `dict(entry["ycsb"])`、perf は `_perf_for(entry)` |
| `autonomous_trial_completeness.py:2884-2905` | checker も `entry = producer.WORKLOADS[workload]` とし、cell と `dict(entry["ycsb"])` を比較 |
| `autonomous_trial_completeness.py:516-608` | `expected_search_values` の ycsb、records、threads、pilot_scope、spec を同じ entry から導出 |

正式 scale literal は C01 のため、三 sink の各関数本体に独立して残します。共通 helper へ出してはいけません。

```python
records = entry["records"]
threads = entry["threads"]
if entry["profile_selector"] == FORMAL_LEGACY_PROFILE:
    if records != 1_000_000 or threads != 48:
        raise AutonomousTrialError("formal workload scale differs")
```

この検査を `_campaign_for`、`_perf_for`、`_descriptor_for` の各本体に置き、その後の出力には literal ではなく検査済みの `records` / `threads` 変数を使います。

## 2. P1 判定と探索 byte 非回帰

P1 が正しい根拠は現在のデータ流です。

- `p3_autonomous_workload_trial.py:848-870` と `:902-915` は、`WORKLOADS[workload]` を flags として `_campaign_for` へ渡しています。
- `_campaign_for:652-654` は flags と scale を別 field にします。
- `_run_workload:2843-2856` は flags だけを cell に複写し、perf scale は別に構築します。
- `_descriptor_for:702-706` も `{records, threads, ycsb}` の明示射影です。
- Layer-3 の現在の誤りは `autonomous_trial_completeness.py:2903` が entry 全体を flags と仮定している点です。

したがって、構造化後に `dict(entry)` を cell や `ycsb` へ渡す実装が台帳予測の形であり、それは不採用です。

### pin するテスト

`orchestrator/tests/test_p3_autonomous_workload_trial.py:335-374` に探索非回帰テストを追加します。

`test_t1334_exploratory_entry_projects_exact_legacy_bytes` で、A/B/C ごとに以下を独立 literal と比較します。

- `canonical_json(entry["ycsb"])`
- cell に載る `workload_flags`
- `campaign.search_config["ycsb"]`
- `PerfConfig.workload`

期待する canonical bytes は次の形です。

```text
{"ycsb_rmw":"0","ycsb_rratio":"50","ycsb_zipf_skew":"0.9"}
{"ycsb_rmw":"0","ycsb_rratio":"95","ycsb_zipf_skew":"0.9"}
{"ycsb_rmw":"0","ycsb_rratio":"100","ycsb_zipf_skew":"0.9"}
```

同じテストで次も pin します。

- `PerfConfig` を `dataclasses.asdict` した canonical bytes が、`records=100_000`、`threads=4`、`extime=1`、`reps=2` の旧期待値と一致する。
- `_descriptor_for(entry)` の descriptor canonical bytes と projection record が既存 golden と一致する。
- `ident.canonical_preimage(cfg).encode()` を、entry から再導出しない独立した旧期待 object の canonical bytes と直接比較する。
- 既存 `_CURRENT_NO_BUILD_CAMPAIGN_ID` および A/B/C campaign epoch constants は変更しない。

さらに以下の既存テストを非回帰 control として維持します。

- `test_no_build_campaign_identity_binds_shared_policy_context`
- `test_generation_one_payload_bytes_are_exactly_legacy_shape`
- `test_t428_workload_campaign_epoch_and_old_root_nonwrite`
- `_golden_cell_metadata` と `_layer3_campaign` が持つ A/B/C descriptor / campaign golden

探索側の期待値を更新する必要が出た場合、それは実装の誤りです。

## 3. 正式 profile、三 sink の実射影、repo scan

正式 entry の ycsb は必ず `s8b_holdout_freeze.HOLDOUTS` の実行時 object から取得します。producer に正式比率、skew、rmw の組を再記述しません。

三 sink の実射影は新規テスト `test_t1333_formal_entry_is_projected_by_all_three_sinks` で検査します。

- `_campaign_for(entry)` の `records / threads / ycsb`
- `_perf_for(entry)` の `records / threads / workload`
- `_descriptor_for(entry)` の `descriptor.scale` と projection record
- 上記三つが entry と一致し、正式 entry では `1_000_000 / 48` になること

literal を単に置いただけではないことは、二段のテストで示します。

1. 探索 profile の合成 entry を `records=123_457`、`threads=13` として三 sink に渡し、三つともその値を出すことを確認する。これで出力側の hardcode を殺す。
2. 正式 profile と表示した entry の records または threads を改変し、各 sink が `AutonomousTrialError` で拒否することを確認する。これで formal literal と実入力の接続を殺せなくする。

`test_t1310_producer_source_has_no_holdout_conjunction` では producer file 本文だけを `s8b_holdout_freeze.holdout_conjunction_hits` に渡し、全 holdout の hit が空であることを pin します。テスト自身にも正式三軸 literal を静止させず、`HOLDOUTS` から期待名を導出します。

## 4. T-1349 の三者関係と assert レベル

三者は同一性の水準が異なります。

| 対象 | 要求する関係 |
|---|---|
| module 表と producer entry | `producer_entry["ycsb"] is HOLDOUTS[name]["ycsb"]` |
| module 表と producer の四 key 射影 | canonical bytes 同値 |
| legacy freeze と module 表 | `candidate_id / records / threads / ycsb` の四 key 射影だけ canonical bytes 同値 |
| legacy freeze 全 entry と module entry | 同値を要求しない。legacy は `unknownness_check` / `variant_binding` を含む上位集合 |
| producer descriptor と arm resolver の own/on descriptor | canonical descriptor bytes と content digest 同値 |

`p3_autonomous_workload_trial.py:191-195` 付近に四 key 射影 helper を置きます。

```python
def _holdout_projection(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": entry["candidate_id"],
        "records": entry["records"],
        "threads": entry["threads"],
        "ycsb": dict(entry["ycsb"]),
    }
```

正式 selector の解決時に、`load_legacy_freeze(ROOT)` の `document["holdouts"][name]`、module entry、producer entry の三つをこの helper に通し、`_canonical_json_bytes` の完全一致を要求します。対象は選択された一 workload だけでなく正式 profile 全体です。失敗は run root 作成や campaign identity 発行より前にします。

さらに `_descriptor_for(producer_entry)` を実際に呼び、`s8c_arm_inputs._descriptor_for_candidate(candidate_id):409-421` の own descriptor と canonical bytes、content digest が一致することを要求します。既知 digest もテストで pin します。

- rr80: `80501db0235d88314edd4a4c29a1949e67acc2b466ae426fbbb1cb3da4b7d843`
- rr20: `53230b8b1f0e0d82def3c384f4d8d8b050a1ce872afd2ed9e2a403c61c3c550b`

注意点として、off と swapped arm の選択済み descriptor は意図的に own workload descriptor と異なります。したがって、実行中の `arm_execution.content_digest_sha256` と producer own descriptor を全 arm で比較してはいけません。

- on: producer own digest と selected arm digest の完全一致を要求。
- swapped: selected digest は derangement 先 entry の digestとして `_check_arm_digest_chain:719-874` が束縛。
- off: neutral artifact digest を既存 arm-chain が束縛。
- 全 arm: descriptor の scale は producer entry の records / threads と一致させる。

これにより T-1349 を恒真な同じ object の自己比較にしません。

## 5. legacy-v1 provenance と non-certifying

`load_legacy_freeze:1376-1394` を正式 selector 解決時に実際に呼びます。`load_ratified_freeze:1333-1352` は呼びません。

機械可読な source record は次の exact-key object とします。

```json
{
  "schema_version": "p3-workload-profile-source/v1",
  "selector": "formal-holdout-legacy-v1",
  "source": "legacy-v1",
  "loader": "s8b_ratified_freeze.load_legacy_freeze",
  "path": "output/s8b-freeze/holdout_freeze.json",
  "sha256": "315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688"
}
```

producer 側で path や hash を再記述せず、`V1_FREEZE_PATH:64`、`LegacyFreeze.sha256:759-766` から構築します。

配置先は次の三つです。

- `p3_autonomous_workload_trial.py:3494-3523` の formal `run-start.workload_profile`
- `p3_autonomous_workload_trial.py:2637-2689` の最終 `report.workload_profile`
- `_campaign_for:650-660` の formal `search_config.workload_profile`

最後の field は campaign identity preimage に入り、`layer3_report.py:538-560` により `layer3_report.workload.workload_profile` へそのまま射影されます。探索 profile ではこの field を完全に省略し、既存 identity bytes を保存します。

新しい `certifying` flag は profile record に作りません。non-certifying は既存の次の chain で表します。

- `trial_registry.TrialLaunchAdmission.certifying:183-194` が `False`
- `launch_admission.reason_code == "registered-effective-non-certifying"`
- `autonomous_trial_completeness.py:1550-1575` が producer に `certifying=False` を強制
- `layer3_report.py:538-560` が通常 report に `certifying_input=False`
- `autonomous_trial_completeness.py:2959-2963` が Layer-3 値と launch admission を一致させる

新しい completeness 検査は、formal source record が run-start、report、campaign search config で byte 同値であること、および同じ run の既存二つの certification field がともに false であることを要求します。

formal report の `claim_scope.label` も `"legacy-v1 formal-scale run; non-certifying"` 相当へ切り替えます。`scientific_claim` は引き続き false です。探索 label と report key set は変更しません。

## 6. 明示 selector と `--workloads`

`p3_autonomous_workload_trial.py:3732-3743` に次を追加します。

```text
--workload-profile
```

- choices: `exploratory-ycsb-abc`, `formal-holdout-legacy-v1`
- default: `exploratory-ycsb-abc`
- `run_trial` の keyword 引数も同じ default
- plain str かつ closed set でない selector は `AutonomousTrialError`
- CLI の未知値は argparse error
- programmatic API の未知値も run root 作成前に fail closed

`--workloads` の default は現在の `list(WORKLOADS)` から `list(DEFAULT_WORKLOADS)` へ変えます。正式 entry を `WORKLOADS` に追加しても既定起動が五 workload へ拡大しないためです。

`_parse_workloads:3718-3729` は全 producer entry を字句的に受け入れます。その後に selector と workload 集合を照合します。

- exploratory selector: A/B/C のみ
- formal selector: HOLDOUTS 由来の workload 名のみ
- mixed profile は拒否
- formal selector でも registry / manifest gate は従来どおり必須
- manifestless holdout の U4 gate を保つため、selector 名の closed-set 検査は先に行う一方、workload/profile 整合検査は既存 registry admission 後、campaign identity 前に置く

`main:3802-3845` は selector を CLI preflight と `run_trial` の双方へ渡し、fresh rederivation でも同じ selector / source record を要求します。

## 7. `pilot_scope`

正式 profile に探索値を再利用してはいけません。採用値は selector と同じ次の値にします。

```text
formal-holdout-legacy-v1
```

変更箇所は次のとおりです。

- `_campaign_for:659`: `entry["pilot_scope"]`
- `_common_payload:1901-1918`: `entry["pilot_scope"]`
- `validate_planner_payload` 呼び出し `:2960-2970`: `expected_pilot_scope=entry["pilot_scope"]`
- `validate_coder_payload` 呼び出し `:3018` 付近: 同上
- `autonomous_trial_completeness.py:571-586`: campaign lock の期待値を entry から導出
- `autonomous_trial_completeness.py:1139-1155`: receipt の fixed literals を workload entry から導出
- `s8c_generation_projection.py:20`: 探索単独 constant を二つの closed values に分離
- `s8c_generation_projection.py:621-654`: `_validate_common_payload` に必須 `expected_pilot_scope`
- `s8c_generation_projection.py:734` / `:818`: planner / coder validator に同引数を追加

generation projection は任意文字列を許可せず、期待値自身が closed set 内であることと payload との exact equality の双方を要求します。

追加テストは以下です。

- `test_formal_pilot_scope_is_accepted_only_when_explicitly_expected`
- `test_formal_payload_with_exploratory_expected_scope_is_rejected`
- `test_exploratory_payload_bytes_remain_unchanged`

## 8. Layer-3 の導出

`autonomous_trial_completeness.py:516-608` の `_check_cell_campaign_identity` は `workload_flags` ではなく `entry` を受け取る形にします。

```python
expected_search_values = {
    # 既存固定 policy fields
    "pilot_scope": entry["pilot_scope"],
    "records": entry["records"],
    "threads": entry["threads"],
    "workload": workload,
    "ycsb": dict(entry["ycsb"]),
}
```

formal entry だけ `workload_profile` を expected key/value に加えます。これは別 checker profile 表を持つ「形 2」ではありません。producer の単一 entry と report に記録された source recordだけを使います。

campaign-chain loop `:2884-2905` は次を要求します。

- workload が `producer.WORKLOADS` に存在
- `cell.workload_flags == dict(entry["ycsb"])`
- campaign search scale / pilot scope が entry と一致
- descriptor scale が entry と一致
- formal source record が report / campaign で一致
- registered descriptor の content digest は引き続き `_check_arm_digest_chain:719-874` で arm authority と一致

探索用 `_AUTONOMOUS_SEARCH_CONFIG_KEYS:123-128` の集合自体は変えず、formal のときだけ source key を追加することで探索 preimage を保存します。

## 9. C01 の遷移

`_evaluate_c01:1414-1445` の順序は明確です。

1. `:1423-1424` で三 sink 各本体に `1_000_000` と `48` があるか検査。
2. `:1425-1429` で main から三 sink / run_trial への到達性を検査。
3. `:1430-1440` で、宣言 path の `load_ratified_freeze` 呼び出しと `sha256` / `holdouts` 属性を要求。

本実装では 1 と 2 は通りますが、呼ぶのは `load_legacy_freeze` です。したがって実装後も status は正しく `UNSATISFIED` のままで、reason_code だけ次へ遷移します。

```text
workload-projection-mismatch
    ->
ratified-generation-reference-absent
```

`orchestrator/tests/test_s8c_preregistration_predicates.py:151` の C01 snapshot だけを更新します。

`TOKEN_ONLY_C01:395-415` と `_negative_control_case:594-608` は更新しません。特に perf sink を `100_000` へ戻す負の control は、そのまま C01 の scale tripwire として残します。

## 10. 変異事前登録

以下の旧字面を mutation patch の anchor とします。

1. `p3_autonomous_workload_trial.py:191`

   旧字面: `WORKLOADS: dict[str, dict[str, str]] = {`

   変異: nested entry を旧 flat flags へ戻す、または cell へ entry 全体を載せる。

   赤にする検査: `test_t1334_exploratory_entry_projects_exact_legacy_bytes`、formal entry schema test。

2. `_campaign_for:652-659`

   旧字面:

   ```python
   "ycsb": dict(workload_flags),
   "records": 100_000,
   "threads": 4,
   ...
   "pilot_scope": "exploratory-ycsb-abc",
   ```

   変異: 新実装をこの旧 hardcode に戻す。

   赤にする検査: formal three-sink projection、synthetic scale projection、formal pilot scope、formal Layer-3 chain。

3. `_perf_for:691-698`

   旧字面:

   ```python
   return PerfConfig(
       records=100_000,
       threads=4,
       workload=dict(workload_flags),
       extime=1,
       reps=2,
   )
   ```

   変異: entry 読取を上記へ戻す。

   赤にする検査: formal PerfConfig projection、synthetic scale projection、既存 C01 negative control。

4. `_descriptor_for:701-706`

   旧字面:

   ```python
   projected_input = {
       "records": 100_000,
       "threads": 4,
       "ycsb": dict(workload_flags),
   }
   ```

   変異: entry 読取を上記へ戻す。

   赤にする検査: formal descriptor scale、T-1349 descriptor digest、formal scale tamper rejection。

5. `autonomous_trial_completeness.py:2903-2905`

   旧字面:

   ```python
   workload_flags = producer.WORKLOADS[workload]
   if cell.get("workload_flags") != workload_flags:
   ```

   変異: nested entry 全体を flags として扱う。

   赤にする検査: exploratory campaign-chain control、formal campaign-chain positive control。

6. `autonomous_trial_completeness.py:576-585`

   旧字面: `"pilot_scope": "exploratory-ycsb-abc"`, `"records": 100_000`, `"threads": 4`, `"ycsb": dict(workload_flags)`。

   変異: entry 導出を旧固定値へ戻す。

   赤にする検査: formal campaign-chain scale / scope mutation tests。

7. `_prepare_campaign_identity:848-870`

   旧字面では registered branch が `_descriptor_from_arm_execution(arm_execution)` だけを読み、module / legacy / producer の own profile 比較がありません。

   変異: 四 key canonical bytes assert または own descriptor digest assert を削除。

   赤にする検査: producer entry の records、threads、ycsb を一つずつ差し替える T-1349 tests。

8. `run-start:3494-3523`

   旧字面は `"scientific_claim": False` の次が `"launch_admission": ...` で、source field がありません。

   変異: `workload_profile` を削除、path/hash/source の一 field を変更、または campaign search config だけから削除。

   赤にする検査: formal source record exactness、run-start/report/campaign byte-chain。

9. `main:3741`

   旧字面: `parser.add_argument("--workloads", type=_parse_workloads, default=list(WORKLOADS))`

   変異: selector を削除、未知 selector を受理、または default を formal にする。

   赤にする検査: CLI default exploration、unknown selector、mixed profile、default workload list。

10. `s8c_generation_projection.py:20` と `_common_payload:1907`

    旧字面: `PILOT_SCOPE = "exploratory-ycsb-abc"` および `"pilot_scope": "exploratory-ycsb-abc"`。

    変異: formal payload に探索 scope を再利用する。

    赤にする検査: formal/exploratory cross-scope rejection。

11. producer sourceへ正式 read 比率 literal を追加する変異。

    赤にする検査: `test_t1310_producer_source_has_no_holdout_conjunction`。records / threads だけの追加は赤にしません。

## 11. 既存テストへの静的波及

直接 fixture、引数、期待値の更新が必要になる既存テストは次です。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py`
  - `test_no_build_campaign_identity_binds_shared_policy_context`
  - `test_run_workload_other_build_reaches_drive_positive`
  - `test_run_workload_rejects_actual_existing_campaign_state`
  - `test_run_workload_accepts_actual_fresh_campaign_layout`
  - `test_prepare_campaign_identity_exactly_matches_existing_derivation`
  - `test_manifest_identity_preflight_does_not_consume_coder_authority`
  - `test_t1311_registered_identity_consumes_issued_arm_bytes`
  - `test_t1311_registered_workload_binds_proposal_and_all_invocations`
  - `test_public_cli_holdout_opt_in_reaches_u4_gate_without_workload_patch`
  - `test_m04_programmatic_holdout_reaches_u4_gate_before_unknown_workload`
  - `test_p10_cli_manifest_gate_precedes_build_preparation_and_forwards_manifest`
  - `test_t1185_m5_cli_default_generation_is_rejected_before_identity_or_run_root`
  - `test_m23_prime_run_trial_registry_gate_rejects_before_run_root`
  - `test_m24_cli_registry_gate_rejects_before_build_preparation`
  - `test_run_trial_rejects_every_dataclass_replace_binding_field`
  - `test_run_trial_rejects_head_move_after_cli_binding`
  - `test_m13_prime_public_launcher_rejects_producer_campaign_derivation_bypass`

  `t325_registered_trial` fixtureでは、旧 flat `WORKLOADS` monkeypatch を削除し、temporary repo に canonical V1 freeze bytes を配置して formal selector から profile を解決します。`_t325_run` は formal selector を既定引数へ加えます。

- `orchestrator/tests/test_autonomous_trial_completeness.py`
  - `test_t428_workload_campaign_epoch_and_old_root_nonwrite`
  - `test_t1311_registered_digest_chain_positive_control`
  - `test_t1311_registered_arm_execution_is_required_exact_and_sha256`
  - `test_t1311_registered_run_rejects_one_missing_digest`
  - `test_t1311_persisted_file_verifier_runs_registered_digest_chain`
  - `test_t1311_registered_digest_chain_rejects_each_bound_sink`
  - `test_t1311_proposal_artifact_is_run_bound_canonical_and_hashed`
  - `test_t1311_origin_terminal_projection_requires_current_arm_epoch`
  - `test_t1311_authoritative_run_root_rejects_coordinated_tree_rebinding`
  - `test_t1311_registered_build_keeps_artifacts_bound_to_trial_run_root`

  `_registered_digest_chain_trial` の campaign lock は正式 scale、正式 pilot scope、source record へ更新します。これは正式 preimage が意図的に変わるためで、探索 golden は更新しません。

- `orchestrator/tests/test_s8c_generation_projection.py`
  - `test_payload_validators_accept_finite_external_metric_snapshots`
  - `test_planner_generation_one_preserves_existing_key_set`

  共通 `_validate_planner` / `_validate_coder` helper に `expected_pilot_scope` を渡すため、これら以外の helper 利用テストの期待値は変えません。

- `orchestrator/tests/test_s8c_preregistration_predicates.py`
  - `test_current_repository_gap_reason_snapshot_requires_cross_wave_review`

  C01 reason のみ更新します。負の control は無変更です。

- `orchestrator/tests/test_layer3_report.py`
  - `test_completeness_rejects_certifying_historical_admission`
  - `test_completeness_reads_contract_from_v2_authority_and_identity_excludes_it`

  fake producer の `WORKLOADS` を nested entry にします。

- `orchestrator/tests/test_reflux_originless_compatibility.py`
  - `test_originless_harness_rebuild_is_deterministic_control`
  - `test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set`

  formal selectorを `_bundle` に渡し、新しい profile/source/scope fields を compatibility projector で明示的に消費してから旧 baseline と比較します。旧 baseline を正式 scale の新 bytes で上書きしてはいけません。

- `orchestrator/tests/test_trial_registry.py`

  `_fixture_campaign_identity`、`_complete_report`、`_reports` が正式 campaign preimage と source record を構築しているため、少なくとも次の `_reports` 利用テストへ波及します。

  `test_p5_six_complete_terminal_reports_pass_acceptance`、`test_t822_acceptance_allows_coherent_past_measurement_head`、`test_t1185_pa_all_six_generation_two_reports_pass_acceptance`、`test_acceptance_projects_identical_terminal_bytes_in_all_json_boundaries`、`test_acceptance_independently_requires_exact_rederived_launch_admission`、`test_acceptance_independently_rederives_historical_arm_execution`、`test_acceptance_rejects_cell_descriptor_that_differs_from_arm_input`、`test_acceptance_registered_run_rejects_one_missing_digest`、`test_acceptance_runs_digest_chain_once_per_registered_trial`、`test_acceptance_rejects_null_or_open_origin_binding_projection`、`test_acceptance_rederives_each_self_consistent_launch_binding_field`、`test_p7_later_registry_rows_do_not_hide_older_manifest`、`test_m10_acceptance_rejects_missing_lifecycle_terminal`、`test_acceptance_rejects_start_run_root_outside_report_parent`、`test_m11_acceptance_receipt_is_exclusive_create`、`test_acceptance_v1_has_no_certifying_issuance_branch`、`test_p12_accept_cli_runs_from_clean_pythonpath`、`test_m16_report_prereg_binding_is_required`、`test_m17_measurement_registry_must_already_contain_registration`、`test_m20_report_trial_set_rejects_duplicate_or_foreign`、`test_m21_terminal_ratio_and_campaign_projection_is_bound`、`test_m22_existing_completeness_verifier_is_mandatory`、`test_m28_report_only_binding_without_run_start_binding_is_rejected`、`test_m29_intermediate_committed_rewrite_is_rejected_by_history_walk`。

正式 manifest campaign IDs の更新根拠は scale、pilot scope、source provenance が identity-bound になることです。単なる golden 更新にはしません。

`output/s8b-freeze/holdout_freeze.json`、`V1_FREEZE_SHA256`、`s8b_holdout_freeze.HOLDOUTS`、`trial_registry.HOLDOUT_BINDINGS` は編集しません。したがって frozen artifact の既存 pin を変更する根拠はありません。

## 総括

- P1 の ycsb-only 射影が正しく、探索 cell、PerfConfig、descriptor、campaign preimage は byte 不変にできます。
- 正式 entry は HOLDOUTS から作り、三 sink が entry scale を実際に使いながら各本体で `1_000_000 / 48` を検査します。
- legacy、module 表、producer は四 key canonical bytes と own descriptor digest で束縛し、認証状態は既存 false chainを使います。
- 未解決の裁定はなく、最大の実装リスクは正式 campaign ID と registry compatibility fixture の一括再導出です。