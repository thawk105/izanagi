# T-529 file:line 実装プラン

結論として、`GENERATIONS` の末尾ではなく、連番・hash-chain 化した activation record から `REGISTRY` を構成し、入口では同一状態から発行した sealed in-memory receipt を最初の書込み直前に再検査する構成を推奨する。

ただし、暫定 P3 はそのまま実装不能である。現行 `linux-baremetal` g1 は `acquisition_receipt` を持たない legacy calibration であり、厳密適用すると現行受理集合を壊す。この例外と、実在しない「silo 昇格入口」は親の裁定が必要である。

以下は静的検査結果と実装予定を区別して記す。pytest は実行しておらず、緑は主張しない。worktree は静的調査後も clean である。

## 1. activation record の設計

### 置き場所

単一の上書き可能ファイルでは serial の単調性や rollback を検査できないため、create-only の連番 record 群にする。

```text
orchestrator/campaign/env_contract_activation.py
orchestrator/campaign/env_contract_activations/
└── 00000001.json
tools/issue_env_contract_activation.py
```

`GENERATIONS` と env 固有 literal は引き続き [env_contract.py:231-275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:231) が唯一の所有者とする。新 module は record の解釈と evidence 検証だけを担い、D176 が却下した registry の二重化にはしない。[decisions.md:8700-8706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/docs/decisions.md:8700)

### JSON schema

各 `NNNNNNNN.json` の exact key 集合を次に固定する。

| key | exact 型・制約 |
|---|---|
| `schema_version` | `str`、値は `"env-contract-activation/v1"` |
| `activation_serial` | exact `int`、`>=1`。`bool` は拒否 |
| `previous_activation_state_sha256` | serial 1 だけ `null`、以後は lowercase hex64 |
| `active_contracts` | 非空 `list`。`env_tag` 昇順、重複なし |
| `activation_state_sha256` | lowercase hex64 |

`active_contracts` の各要素は exact に次の3 keyだけを持つ。

| key | exact 型・制約 |
|---|---|
| `env_tag` | canonical slug の `str` |
| `generation` | exact positive `int` |
| `contract_sha256` | lowercase hex64 |

追加の時刻、issuer 自己申告、自由文は入れない。`contract_sha256` が `CalibrationRef` を含む全契約 field を既に束縛するため、calibration path/hash を record に重複させない。[env_contract.py:145-160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:145)

`activation_state_sha256` は、それ自身を除く4 keyの canonical JSON、すなわち `sort_keys=True, separators=(",", ":"), ensure_ascii=True` の SHA-256 とする。全 record bytes も canonical one-line JSON + LF に固定する。

初期 record は両 env の g1 を選ぶ。提案 schema から静的に算出した初期 state hash は次になる。

```text
f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed
```

### JSON を選ぶ理由

Python literal は `ast.literal_eval` を使っても duplicate key が dict 化時に消え、tuple/list、`True`/`1` 等の Python 固有差を持ち込む。JSON は以下を一つの検査面で閉じられる。

- duplicate key と非有限数の拒否
- exact key 集合
- canonical bytes
- 他言語からも確認可能
- code execution を伴わない

### 生成者

`tools/issue_env_contract_activation.py` を新設し、maintainer が明示的に実行する。calibration publisher から自動活性化はしない。

予定する動作は以下。

1. 現 chain を strict に検証する。
2. 次の `activation_serial` と predecessor hash を機械導出する。
3. 選択された全 `(env_tag, generation)` の publish evidence を検証する。
4. `NNNNNNNN.json` を `O_EXCL` で create-only 生成する。
5. maintainer が diff と calibration receipt を確認して commit する。

既存 publisher も、`quality.status != "accepted"` なら publish せず、accepted artifact だけを `registered/calibration-<digest-prefix>.json` へ no-replace publishしている。[cli.py:772-821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/calibrator/cli.py:772)

### runtime 検査

新規 `env_contract_activation.py` は次の行割りを予定する。

- `:1-39` — constants、error、sealed dataclass
- `:40-102` — duplicate-aware JSON decoder と canonical-byte 検査
- `:103-157` — exact schema、filename/serial、hash-chain 検査
- `:158-244` — `verify_activation_evidence()`
- `:245-302` — `load_activation_state()`
- `:303-340` — `issue_receipt()` / `assert_current_receipt()`

`verify_activation_evidence()` は各 active row に対して次を要求する。

1. `GENERATIONS[env_tag]` に exact generation が存在する。
2. record の `contract_sha256` がその `GenerationEntry.contract.contract_sha256` と一致する。
3. calibration path が repo 内に閉じ、同一 bytes を一度だけ読む。
4. bytes SHA-256 が contract の `calibration_ref.sha256` と一致する。
5. required-mode は path が exact に  
   `output/env/<env_tag>/calibration/registered/calibration-<sha[:16]>.json`
   である。
6. `schema_v2.validate_calibration_v2(raw)` を通る。
7. `quality.status == "accepted"` である。

既存の根拠は以下。

- repo confinement、存在、bytes hash: [env_attestation.py:1060-1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_attestation.py:1060)
- duplicate-aware exact v2 parse: [schema_v2.py:724-772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/calibrator/schema_v2.py:724)
- `acquisition_receipt` exact keys: [schema_v2.py:555-567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/calibrator/schema_v2.py:555)、[schema_v2.py:611-627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/calibrator/schema_v2.py:611)
- accepted 時の provenance/cross-field 条件: [schema_v2.py:521-544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/calibrator/schema_v2.py:521)

したがって、record だけを g2 に書き換えても、`verify_activation_evidence()` が未知 generation、非実在 path、hash 不一致、staging path、receipt 欠落、rejected quality のいずれかで拒否する。既に正規 publish 済みの有効な g2 が存在する場合に record 更新で切り替わるのは、意図した活性化操作である。

### P3 の必要な訂正

現行 `linux-baremetal` artifact は legacy 形で、先頭から `env_tag`、`threads`、`clocks_per_us` を持つが `schema_version` と `acquisition_receipt` を持たない。[legacy calibration:1-17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:1)

既存 loader も exact SHA 一件だけを grandfather している。[env_attestation.py:28-35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_attestation.py:28)、[env_attestation.py:1119-1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_attestation.py:1119)

よって P3 は次のどちらかに修正しなければならない。

- 推奨: `linux-baremetal` g1 の exact contract hash  
  `1b2ee853...fa1dc7` だけを legacy 例外とする。mode-none の別 contract/g2 には一般化しない。
- 代案: legacy bytes に対する detached acquisition evidence を新設する。新たな evidence schema と発行根拠が必要になり、この wave の範囲が広がる。

例外なしでは初期 record 自体が import 時に拒否され、要求された positive control は成立しない。

また、mode-none loader は現在この一つの SHA しか受理しないため、linux の新 calibration g2 は activation record だけ整備しても実行不能である。[test_env_contract.py:818-831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_env_contract.py:818) これは T-529 だけでは解消しない。

## 2. 権威導出の置換

### `validate_generations`

[env_contract.py:316-326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:316) の `len(sequence) != 1` loop を削除し、`validate_generations()` は [env_contract.py:278-313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:278) の構造・連番・successor・hash 一意性検査だけを行う関数に戻す。

防壁を単に外すのではなく、module 初期化を次の順序に置換する。

```python
GENERATIONS = ...
validate_generations(GENERATIONS)
_ACTIVATION_STATE = load_activation_state(GENERATIONS, ...)
_CONTRACT_SHA256_INDEX = _build_contract_sha256_index(GENERATIONS)
REGISTRY = MappingProxyType({
    env_tag: active_entry.contract
    for env_tag, active_entry in _ACTIVATION_STATE.active_entries.items()
})
```

挿入点は現行 [env_contract.py:344-352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:344)。`_CONTRACT_SHA256_INDEX` は inactive/historical generation を含む全世代 index のまま維持する。

これにより、

- source に g2 を追加しただけなら record は g1 を選び続ける。
- record が未登録 g2 を選べば import が失敗する。
- record が g2 を選んでも publish evidence が不正なら import が失敗する。
- `REGISTRY` の公開形は引き続き `MappingProxyType[str, ExecutionEnvironmentContract]`。
- `lookup(env_tag)` の signature と unknown-env failure は不変。[env_contract.py:383-390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:383)

### receipt API

`env_contract.py` の `lookup()` 後、現行 line 390 付近へ次を追加する。

```python
def admit_current(env_tag: str) -> tuple[
    ExecutionEnvironmentContract,
    ActivationReceipt,
]: ...

def assert_current_activation(
    receipt: ActivationReceipt,
    contract: ExecutionEnvironmentContract,
) -> None: ...
```

receipt の public exact field は次の6個とする。

```text
schema_version: "env-contract-activation-receipt/v1"
activation_serial: exact positive int
activation_state_sha256: lower hex64
env_tag: str
generation: exact positive int
contract_sha256: lower hex64
```

内部には非直列化 `_seal` を持たせる。receipt の型そのものを権威にはせず、`assert_current_activation()` が module の canonical `_ACTIVATION_STATE` と全 field を再照合する。これは「public dataclass を包み直しても権威にならない」という D176 の境界に従う。[decisions.md:8680-8683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/docs/decisions.md:8680)

### `contract_sha256` を1 bitも動かさない保証

以下は編集対象外とする。

- contract field exact 集合: [env_contract.py:97-102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:97)
- `_canonical_obj()`: [env_contract.py:145-148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:145)
- hash algorithm: [env_contract.py:150-160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:150)

既存の独立 golden は linux が [test_env_contract.py:1109-1122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_env_contract.py:1109)、Pegasus が [test_env_contract.py:1125-1138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_env_contract.py:1125)。両方を変更せず残す。

brief の `test_env_contract.py:58` と `:263` は contract hash ではなく calibration SHA である。generation contract hash の凍結値は [test_env_contract.py:69-75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_env_contract.py:69) にある。

### 現状受理集合の positive control

新規 nodeid 候補:

```text
orchestrator/tests/test_env_contract_activation.py::
  test_g1_activation_preserves_current_lookup_acceptance_set
```

次を一つの test で固定する。

- 全 `GENERATIONS` の長さが1。
- initial record の env 集合が `GENERATIONS` と exact 一致。
- 各 active row が `sequence[0]` を指す。
- `REGISTRY` と `lookup()` が従来と同じ object を返す。
- unknown env の受理集合は増えない。
- linux/Pegasus の contract hash がそれぞれ既存 golden と一致。

既存 positive control として以下も残る。

```text
orchestrator/tests/test_env_contract.py::test_lookup_baremetal_golden
orchestrator/tests/test_env_contract.py::test_lookup_pegasus_golden
orchestrator/tests/test_env_contract.py::test_generation_golden_has_exact_keys_nonempty_columns_and_g1_hashes
orchestrator/tests/test_env_contract.py::test_contract_sha256_matches_independent_reference
orchestrator/tests/test_env_contract.py::test_pegasus_contract_sha256_golden
```

さらに synthetic g2 を `GENERATIONS` に置いても g1 record のまま current が変わらない test を追加する。

```text
orchestrator/tests/test_env_contract_activation.py::
  test_registered_but_inactive_g2_does_not_change_registry
```

## 3. 入口6種の確定と訂正

### 3.1 floor

#### `pegasus_floor_scoping.py`

これは自ら「certified consumer へ配線しない調査値」と明記しており、正式な floor 入口ではない。[pegasus_floor_scoping.py:1-5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/pegasus_floor_scoping.py:1)

ただし測定成果物を書くため、親の floor 範囲に残すなら gate 対象にする。

- 最初の書込み: `main()` が `_prepare_out_dir()` を呼ぶ [pegasus_floor_scoping.py:235-241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/pegasus_floor_scoping.py:235)。具体的書込みは `out_dir.mkdir()` の line 121。
- 現 seam: `lookup` は import 済みだが [pegasus_floor_scoping.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/pegasus_floor_scoping.py:23)、calibration 検査は directory 作成後の line 207。現状は遅い。
- 修正: `main()` の line 240 より前に `admit_current(ENV_TAG)` と `assert_current_activation()` を行い、contract を `_run_scoping()` へ渡す。
- schema: producer は top-level dict を組むだけ [pegasus_floor_scoping.py:184-196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/pegasus_floor_scoping.py:184)。test も nested key の包含 `>=` しか見ておらず、exact top schema はない。[test_pegasus_floor_scoping.py:173-183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_pegasus_floor_scoping.py:173)

#### 正式 `s8b_floor_campaign.py`

- Pegasus の最初の書込み: `campaign_claim.acquire_claim()` line 2881。具体的 `O_CREAT|O_EXCL` は [campaign_claim.py:167-216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/campaign_claim.py:167) の line 195。
- non-single-process の最初の書込み: `_fresh_run_dir()` 呼出し line 2920、具体的 `mkdir/os.mkdir` は [s8b_floor_campaign.py:3171-3188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_campaign.py:3171)。
- seam: protocol validation、lookup、calibration read-once、execution receipt が既に line 2750-2785 に集中している。[s8b_floor_campaign.py:2739-2785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_campaign.py:2739) ここで `admit_current()` の receipt を取得し、line 2859 の claim branch 直前に再検査する。公開 resolver injection parameter は追加しない。official mode は既存の非default seam 注入を拒否している。[s8b_floor_campaign.py:2670-2698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_campaign.py:2670)
- schema:
  - floor protocol は exact top key 検査を持つ。[s8b_floor_contract.py:34-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_contract.py:34)、[s8b_floor_contract.py:114-117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_contract.py:114)
  - execution receipt v1 は exact [s8b_floor_campaign.py:901-907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_campaign.py:901)、v2 は [execution_guard.py:363-406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/execution_guard.py:363)。
  - floor artifact 自体の top-level は閉じていない。`config` と `floors` の extra key は拒否するが [s8b_floor_stats.py:486-499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_stats.py:486)、top-level exact set はない。

`write_protocol_document()` は別の authoring utility で、実 freeze namespace への書込みを拒否する。[s8b_floor_campaign.py:506-524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_campaign.py:506) runtime floor 入口には数えない。

### 3.2 oracle

- 最初の書込み: `run_block()` の `_acquire_g12_claim()` line 1193。[s8b_oracle_driver.py:1181-1199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_driver.py:1181) 具体的 claim write は helper line 898。
- seam: `_prepare_v2_execution()` が lookup、contract hash、calibration、execution receipt をまとめる既存 preflight。[s8b_oracle_driver.py:737-845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_driver.py:737) `_V2Plan` line 699-711 に activation receipt を追加し、claim の前に検査する。
- 現 T080 recheck は claim 後の line 1206-1214 なので、activation の模倣先にはしない。activation check は line 1193 より前でなければならない。
- schema:
  - oracle manifest top は exact。[s8b_oracle_manifest.py:34-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_manifest.py:34)、[s8b_oracle_manifest.py:834-837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_manifest.py:834)
  - `campaign-start` は必須keyの包含検査だけで extra を許す。[s8b_oracle_report.py:53-65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_report.py:53)、[s8b_oracle_report.py:576-592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_report.py:576)
  - `campaign-terminal` だけは exact top。[s8b_oracle_report.py:593-604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_report.py:593)

### 3.3 P3

- registered trial の最初の書込み: `record_trial_start_once()` line 1965。[p3_autonomous_workload_trial.py:1957-1975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1957)
  - parent directory の最初の生成は [trial_registry.py:562-596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/trial_registry.py:562) の line 594。
  - ledger open/append は [trial_registry.py:1466-1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/trial_registry.py:1466) の lines 1486/1515。
- exploratory trial の最初の書込み: `run_root.mkdir()` line 1975。
- seam:
  - trigger 側には `_lookup = env_contract.lookup` という既存 resolver seam がある。[p3_s4_loop_trigger_gating.py:88-96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/p3_s4_loop_trigger_gating.py:88)
  - direct trigger は contract 解決後、`layout.ensure()` より前に挿入できる。[p3_s4_loop_trigger_gating.py:701-717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/p3_s4_loop_trigger_gating.py:701)
  - しかし `run_trial()` は trigger 到達前に lifecycle/run root を書く。したがって gating module だけの変更は不十分。`run_trial()` が `trigger.resolve_measurement_activation()` を呼び、line 1965 前で検査する。
- schema:
  - lifecycle start は exact keys。[trial_registry.py:72-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/trial_registry.py:72)、reader enforcement は [trial_registry.py:1360-1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/trial_registry.py:1360)。
  - report top は production validator では完全閉包していないが、既存 test が exact set を凍結している。[test_p3_autonomous_workload_trial.py:3110-3119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_p3_autonomous_workload_trial.py:3110)
  - `activation_report_digest_sha256` は preregistration activation の既存別義である。[trial_registry.py:138-149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/trial_registry.py:138) 新 receipt をそこへ流用してはいけない。

### 3.4 適格性 T-126

- 暫定同定の訂正: 最初の書込みは `create_attempt()` line 1009 ではなく、`QualificationRoot.issue()` line 899。[t126_driver.py:898-900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/t126_driver.py:898) root が未作成なら具体的 `mkdir` は [artifacts.py:258-272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/artifacts.py:258) の line 267。
- seam: lookup は line 868 で、最初の write より前に存在する。[t126_driver.py:862-878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/t126_driver.py:862) ここを `admit_current()` に置換し、line 899 直前で receipt を再検査する。public monkeypatch seam は不要。
- 現 calibration attestation は line 1127 まで遅延しているため、activation evidence gate の代用にはならない。[t126_driver.py:439-447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/t126_driver.py:439)
- schema: series result JSON schema は top-level `additionalProperties:false`。[t126_series_result_schema.json:89-97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/t126_series_result_schema.json:89) driver も exact key set を再検査する。[t126_driver.py:1261-1273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/t126_driver.py:1261)

### 3.5 selector

親の3ファイル同定は producer 入口としては誤り。

- `s8b_selector_freeze.main()` は `plan` と `verify` だけで書かない。[s8b_selector_freeze.py:1025-1038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_selector_freeze.py:1025)
- `write_prediction_freeze()` は library writer だが、production caller は [s8b_prediction_runner.py:966-984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_prediction_runner.py:966)。
- 正しい入口候補は `s8b_prediction_runner.seal()`。[s8b_prediction_runner.py:1538-1595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_prediction_runner.py:1538)

詳細:

- 最初の mutating call は `ClaudeHeadlessProvider` 構築中の `artifact_root.mkdir()` line 1100。続いて neutral tmp root を line 1132/1066 で作る。[s8b_prediction_runner.py:1092-1150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_prediction_runner.py:1092)
- seam: `_derive_protocol_bytes()` が `build_protocol_document()` を通じて間接的に current contract を使う。[s8b_prediction_runner.py:1457-1473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_prediction_runner.py:1457) `seal()` の derived/committed protocol 一致後、provider 構築前の lines 1567-1587 に直接 `admit_current(protocol["env_tag"])` を置く。
- schema:
  - journal header は exact。[s8b_prediction_runner.py:77-81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_prediction_runner.py:77)、[s8b_prediction_runner.py:339-365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_prediction_runner.py:339)
  - final prediction freeze も exact。[s8b_selector_freeze.py:73-83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_selector_freeze.py:73)、[s8b_selector_freeze.py:667-680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_selector_freeze.py:667)
  - selector input/output も exact。[s8b_selector_input.py:114-120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_selector_input.py:114)、[s8b_selector_output.py:88-105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_selector_output.py:88)

ただし selector は workload を実行せず、environment attestation も発行しない。狭義の「実行環境入口」なら入口として成立せず、入口数は5になる。一方、current contract を含む floor protocol を再導出して proof-chain artifact を書く producer ではある。brief の「6入口」を維持するなら、この意味に限定して `s8b_prediction_runner.py` を対象とすることを推奨する。

### 3.6 silo

`orchestrator/campaign/silo_ladder_rung1.py` は silo 昇格入口ではない。成果物は exact に次を宣言する。

```text
evaluation_role = ability_probe
research_goal_eligible = false
recovery_measurement_eligibility = false
```

根拠は [silo_ladder_rung1.py:4688-4699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:4688)、validator も同値を要求する。[silo_ladder_rung1.py:1240-1250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:1240)

このファイルの実在 writer を保護するなら3経路すべてが必要。

- `correctness`: 最初の write は `_correctness_command()` の `attempt_dir.mkdir()` line 3743。contract lookup は line 3752 で遅い。[silo_ladder_rung1.py:3741-3753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:3741)
- `gap-job`: 最初の write attempt は `job_staging.mkdir()` line 3984、最初の新規 attempt subtree は line 4000。submit binding 検査は line 4004 で遅い。[silo_ladder_rung1.py:3979-4006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:3979)
- `collect`: 最初の write は `_copy_tree_create_only()` 呼出し line 4528、具体的 destination mkdir は line 3729。[silo_ladder_rung1.py:3726-3738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:3726)、[silo_ladder_rung1.py:4524-4529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:4524)

`_activation_preflight()` を一つ作り、各 command の先頭で呼び、既存の後段 lookup/attestationには同じ contract を渡す。CLI の `verify-result` は read-only なので対象外。

成果物 top-level は exact。[silo_ladder_rung1.py:1224-1232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:1224) `raw_bundle` 等も個別 exact 検査を持つ。[silo_ladder_rung1.py:1440-1467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:1440)、[silo_ladder_rung1.py:1527-1539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:1527)

真の promotion consumer が別にあるなら、その file/function が未同定である。ここへ gate を入れて「silo 昇格を実装した」とは報告してはいけない。

## 4. receipt の形

### 案A: 既存 artifact / journal へ埋め込む

例: oracle `campaign-start`、P3 lifecycle、selector header、T-126 result、silo top-level。

影響:

- 全対象 artifact の bytes、body hash、journal hashが変わる。
- P3、selector、T-126、silo は exact-key schema を改版しない限り即時拒否。
- floor execution receipt v1/v2 も exact なので field 追加不可。
- oracle `campaign-start` だけは extra key を許すが、6入口で形が統一されない。

既存 bytes 不変条件と両立しないため非推奨。

### 案B: `activation-receipt.json` sidecar

各 run namespace に create-only sidecar を置く。

影響:

- 既存 JSON/JSONL ファイル自身の bytes は不変。
- ただし directory/file-set、raw manifest、evidence manifest、campaign identity が変わる。
- claim より先に sidecar を置くと「claim が最初の副作用」という既存規律を壊す。
- directory が未作成の入口では、sidecar 用 directory creation 自体が新たな最初の write になる。
- 途中拒否時に orphan sidecar が残る。

durable audit が必須なら将来 wave で versioned sidecar closure として設計可能だが、この wave には広すぎる。

### 案C: sealed in-memory receipt

`admit_current()` が sealed `ActivationReceipt` を返し、入口の plan/local stateが最初の write まで保持する。write 直前に `assert_current_activation()` を要求する。

影響:

- 既存成果物 bytes: 0 byte
- 既存 exact-key schema: 変更なし
- campaign ID/body hash: 変更なし
- durable な事後証拠: なし

この wave では案Cを推奨する。record 自体が committed activation historyであり、入口 receipt は「同じ activation state を検査したことを writer の制御フローで保証する capability」と限定する。durable receipt を要求するなら、既存 bytes 不変との優先順位を親が改めて裁定する必要がある。

### exact-key 検査の実在箇所

主要箇所をまとめると以下。

- calibration/acquisition: [schema_v2.py:555-567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/calibrator/schema_v2.py:555)
- floor protocol: [s8b_floor_contract.py:114-117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_contract.py:114)
- execution receipt v1/v2: [s8b_floor_campaign.py:901-907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_campaign.py:901)、[execution_guard.py:371-406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/execution_guard.py:371)
- oracle manifest / terminal: [s8b_oracle_manifest.py:834-837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_manifest.py:834)、[s8b_oracle_report.py:593-604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_report.py:593)
- P3 lifecycle: [trial_registry.py:1374-1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/trial_registry.py:1374)
- selector header/final: [s8b_prediction_runner.py:339-345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_prediction_runner.py:339)、[s8b_selector_freeze.py:671-680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_selector_freeze.py:671)
- T-126 result: [t126_series_result_schema.json:89-97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/t126_series_result_schema.json:89)
- silo result: [silo_ladder_rung1.py:1224-1268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:1224)

## 5. pin 閉包

### brief 記載 pin の判定

| 箇所 | 判定 |
|---|---|
| `orchestrator/qualification/contract.py:62` | hard-coded digest ではなく path 集合。run 時に working bytes と `HEAD:<path>` blob をそれぞれ hash して一致させる。[t126_driver.py:346-383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/t126_driver.py:346) artifact 内ではその commit blob digest が固定され、consumer が再計算する。[identity.py:130-152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/identity.py:130) |
| `test_env_contract.py:83` | source digest pin ではない。AST env-literal 免除 region の対象指定。実ファイルを test 時に読み直す。[test_env_contract.py:1172-1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_env_contract.py:1172) |
| `test_env_contract.py:559` | digest ではなく AST 上の module-level call/assignment 順序検査。[test_env_contract.py:557-589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_env_contract.py:557) |
| `test_env_contract.py:1195` | digest ではなく AST positive control。env literal が `_build_registry` に存在することを実行時再走査。[test_env_contract.py:1192-1200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_env_contract.py:1192) |
| `test_silo_ladder_rung1_driver.py:933` | test は path 集合だけを固定。digest は `runtime_modules_binding()` が現在 bytes から再計算する。[silo_ladder_rung1.py:254-280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:254) |
| `test_s8c_preregistration_predicates.py:355` | synthetic source dict 内の fake text。実 `env_contract.py` bytes を参照しない。[test_s8c_preregistration_predicates.py:330-360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_s8c_preregistration_predicates.py:330) |
| `t419_probe_causality.py:3495` | `git status --porcelain` の dirty scope に path を含める。uncommitted edit は `matched=False` にするが digest golden ではない。[t419_probe_causality.py:3491-3517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/tools/pegasus/probes/t419_probe_causality.py:3491) |
| `t419_probe_causality.py:3533` | 現在 bytes の SHA を result に記録するだけ。期待 SHA との比較項目ではない。[t419_probe_causality.py:3518-3537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/tools/pegasus/probes/t419_probe_causality.py:3518) |

committed silo evidence には歴史的な source digest が確かに記録されている。[silo_ladder_rung1.json:67-68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:67) ただし evidence test は current runtime binding と一致しないことを意図的に要求しており、現在 bytes の golden ではない。[test_silo_ladder_rung1_evidence.py:1231-1240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1231)

### 現在 `env_contract.py` の変更で赤くなる test

変更内容依存であり、任意の1 byte、例えば comment だけの変更を必ず赤にする pytest は現状存在しない。

意味・配線を壊した場合に赤くなる主な nodeid は以下。

```text
orchestrator/tests/test_env_contract.py::
  test_generation_golden_has_exact_keys_nonempty_columns_and_g1_hashes
  test_registry_and_lookup_are_generation_tail_view
  test_validate_generations_valid_two_generation_reaches_bootstrap_fuse
  test_module_level_generation_validation_precedes_indexes_and_registry
  test_registry_calibration_refs_are_canonical_hash_bound_and_meaningful
  test_contract_sha256_matches_independent_reference
  test_pegasus_contract_sha256_golden
  test_v2_modules_have_no_env_literals_outside_registry
  test_ast_check_is_not_vacuous_env_contract_has_literals
```

このうち tail-view、bootstrap-fuse、module-order の3 test は本実装で意図的に赤くなるため、activation-view の test へ置換する。

T-126 は pytest golden ではなく、uncommitted source byte drift を実行時に [t126_driver.py:353-370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/t126_driver.py:353) で拒否する。

### 新 dependency の閉包

`env_contract.py` が activation parser、record、`schema_v2` を runtime 使用するため、次を追加する。

- `REQUIRED_CODE_IDENTITY_PATHS` [qualification/contract.py:38-66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/contract.py:38):
  - `orchestrator/campaign/env_contract_activation.py`
  - `orchestrator/campaign/env_contract_activations/00000001.json`
  - `orchestrator/calibrator/schema_v2.py`
- silo runtime binding [silo_ladder_rung1.py:254-280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:254):
  - activation module
  - loader が列挙した全 activation record
- T419 related dirty scope [t419_probe_causality.py:3491-3497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/tools/pegasus/probes/t419_probe_causality.py:3491):
  - activation module
  - activation record directory
  - `schema_v2.py`
- AST neutral module list [test_env_contract.py:78-97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_env_contract.py:78):
  - `env_contract_activation.py` を免除なしで追加

future serial fileを追加した際、T-126 の static required set も同じ commit で増やすことを test で固定する。

## 6. 命名の裁定

静的 `rg -w` 結果:

- `migration_serial`: 0件
- `activation_bundle_sha256`: 0件
- 推奨する `activation_serial`: 0件
- 推奨する `activation_state_sha256`: 0件

字面上の直接衝突はない。ただし暫定名には意味上の衝突がある。

- `migration_*` は既存 T080 の `migration_id` と近く、一回限りの freeze migration を指す。[t080_freeze_migration.py:63-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/t080_freeze_migration.py:63)
- `bundle` は `role_bundle_sha256` [reflux_origin_ledger.py:238-259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/reflux_origin_ledger.py:238) と silo `raw_bundle` [silo_ladder_rung1.py:1224-1229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:1224) の別義が既にある。
- `activation_report_digest_sha256` も preregistration の別概念として存在する。[trial_registry.py:72-75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/trial_registry.py:72)

推奨名は以下。

```text
activation_serial
activation_state_sha256
previous_activation_state_sha256
```

`state` は「全 env の active contract 集合と serial/predecessor を含む状態」の hash であることを正確に表す。`migration` と `bundle` の既存意味を増やさない。

## 7. 段5の2単位分割

### 単位A — activation authority と pin 閉包

先行する。

```text
orchestrator/campaign/env_contract.py
orchestrator/campaign/env_contract_activation.py                 [新規]
orchestrator/campaign/env_contract_activations/00000001.json    [新規]
tools/issue_env_contract_activation.py                          [新規]
orchestrator/qualification/contract.py
tools/pegasus/probes/t419_probe_causality.py
orchestrator/tests/test_env_contract.py
orchestrator/tests/test_env_contract_activation.py              [新規]
orchestrator/tests/test_t126_pegasus_tools.py
orchestrator/tests/test_t419_probe_causality.py
```

責務:

- record schema/chain/evidence
- structural generation validation
- record-derived `REGISTRY`
- receipt API
- contract hash positive controls
- transitive pin closure

### 単位B — 入口配線

単位Aの receipt API に依存する。

```text
orchestrator/campaign/pegasus_floor_scoping.py
orchestrator/campaign/s8b_floor_campaign.py
orchestrator/campaign/s8b_oracle_driver.py
orchestrator/campaign/p3_autonomous_workload_trial.py
orchestrator/campaign/p3_s4_loop_trigger_gating.py
orchestrator/qualification/t126_driver.py
orchestrator/campaign/s8b_prediction_runner.py
orchestrator/campaign/silo_ladder_rung1.py

orchestrator/tests/test_pegasus_floor_scoping.py
orchestrator/tests/test_s8b_floor_campaign.py
orchestrator/tests/test_s8b_oracle_driver.py
orchestrator/tests/test_p3_autonomous_workload_trial.py
orchestrator/tests/test_p3_s4_loop_trigger_gating.py
orchestrator/tests/test_t126_qualification_driver.py
orchestrator/tests/test_s8b_prediction_runner.py
orchestrator/tests/test_silo_ladder_rung1_driver.py
orchestrator/tests/test_env_contract_activation_entrypoints.py       [新規]
```

ファイル所有は素集合である。`qualification/contract.py` は単位A、`t126_driver.py` は単位Bと明示的に分ける。`silo_ladder_rung1.py` 内の runtime binding 追加は入口配線と同じ単位Bで行い、同ファイルを跨がせない。

## 8. 変異事前登録候補

| ID | 壊す箇所 | 変異 | 殺す test 候補 |
|---|---|---|---|
| M01 | [env_contract.py:349-352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:349) | active row ではなく再び `sequence[-1]` を選ぶ | `test_registered_but_inactive_g2_does_not_change_registry` |
| M02 | `env_contract_activation.py:40-157` `[予定]` | duplicate/extra key または非canonical bytes を許す | `test_record_rejects_duplicate_unknown_and_noncanonical_json` |
| M03 | `env_contract_activation.py:103-183` `[予定]` | predecessor、serial gap、filename/serial 不一致を無視する | `test_chain_rejects_gap_rollback_and_bad_predecessor` |
| M04 | `env_contract_activation.py:245-302` `[予定]` | active row 欠落時に generation tail へ fallback する | `test_current_set_requires_exactly_one_row_per_registered_env` |
| M05 | `env_contract_activation.py:158-183` `[予定]` | row の `contract_sha256` と GenerationEntry の一致を外す | `test_active_row_must_match_registered_generation_and_contract_hash` |
| M06 | `env_contract_activation.py:184-220` `[予定]` | path confinement、`registered/`、filename digest prefix、bytes hash のいずれかを外す | `test_missing_staging_escape_or_hash_mismatch_cannot_activate` |
| M07 | `env_contract_activation.py:221-244` `[予定]` | receiptless/rejected v2 を受理する | `test_rejected_or_receiptless_v2_cannot_activate` |
| M08 | [env_attestation.py:1119-1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_attestation.py:1119) と新 legacy gate | legacy 例外を任意 mode-none g2 に広げる | `test_legacy_exception_is_exactly_current_linux_g1_contract`、既存 `test_none_mode_successor_transition_does_not_bypass_loader_grandfather_pin` |
| M09 | [s8b_floor_campaign.py:2859-2881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_campaign.py:2859)、[s8b_oracle_driver.py:1181-1198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_driver.py:1181) | activation check を claim 後へ移す | `test_activation_refusal_precedes_campaign_claim`、`test_activation_refusal_precedes_g12_claim` |
| M10 | [p3_autonomous_workload_trial.py:1963-1978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1963)、[t126_driver.py:898-900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/qualification/t126_driver.py:898) | trigger/attestation 内だけで検査し、lifecycle/root creationを先に許す | `test_activation_refusal_precedes_lifecycle_and_run_root`、`test_activation_refusal_precedes_qualification_root_issue` |
| M11 | [s8b_prediction_runner.py:1564-1588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_prediction_runner.py:1564)、[silo_ladder_rung1.py:3741-3753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/silo_ladder_rung1.py:3741) | provider/mkdir/copy 後に検査する、または silo の3 command中1つを漏らす | `test_activation_refusal_precedes_provider_artifact_root`、`test_each_writer_refuses_before_first_mkdir_or_copy` |
| M12 | `env_contract_activation.py:303-340` `[予定]` | plain dict/手製 dataclass receipt を受ける、serial/hash/contract の一つを照合しない | `test_forged_stale_or_cross_env_receipt_is_rejected` |

first-write test は、writer/claim/mkdir に「呼ばれたら即失敗する tripwire」を置き、activation failure 時に call count が0であることを検査する。production APIへ resolver injection を増やすためではなく、既存注入点または副作用 leaf の spy に限定する。

## 親実測2点の一般化限界

親の実測自体は、次の限定された命題を示している。

1. fresh import が module-level `validate_generations(GENERATIONS)` を通る場合、現 fuse は発火する。[env_contract.py:344-347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:344)
2. structural validationを通る g2 が末尾にあり、`REGISTRY` が `sequence[-1]` のままなら `lookup()` は g2 を current とする。[env_contract.py:278-313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:278)、[env_contract.py:349-352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:349)

次の条件では一般化が破れる。

- module が既に import cache にある、または module-level wiring 自体が回避された場合、fuse 発火の観測は直接一般化できない。
- g2 が連番、env_tag、successor、global contract hash 一意性を満たさなければ、fuse より前の structural validator で落ちる。
- 「current になった」は `lookup()` の意味であり、実行受理まで示さない。
  - official floor は calibration bytesを claim前に読む。[s8b_floor_campaign.py:2758-2785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_campaign.py:2758)
  - oracle も claim前に読む。[s8b_oracle_driver.py:781-803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_driver.py:781)
  - したがって非実在 calibration g2 は両入口で既に write 前拒否される。
- 一方、scoping は out-dir 作成後、T-126 は qualification root 作成後、silo は staging 作成後にしか calibration を検査しない。selector/P3 は同等の calibration admissionを持たない。この非対称性が「共通 activation receipt」を追加する実際の理由である。
- frozen artifact が contract hash で historical resolver を使う経路は、必ずしも current g2 へ切り替わらない。D176 自身も historical resolver の production consumer は未実装と限定している。[decisions.md:8691-8698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/docs/decisions.md:8691)

## 総括

- 推奨骨子:
  - `env_contract_activations/NNNNNNNN.json` の create-only hash-chain。
  - `activation_serial` / `activation_state_sha256` を採用。
  - `REGISTRY` は record が選んだ generation から構築。
  - actual calibration bytes、registered namespace、exact v2 acquisition receipt、accepted quality を import時に検査。
  - 6カテゴリの producer は sealed in-memory receipt を最初の write 前に検査し、既存 artifact bytes/schema は変更しない。
- 最大の実装ブロッカー:
  - P3 を文字どおり適用すると receipt を持たない linux g1 が拒否され、現状受理集合を維持できない。
- scope 上の未解決点:
  - selector は workload 実行入口ではなく proof-chain producer。
  - `silo_ladder_rung1.py` は ability probe で、昇格権限を持たない。
- 親が裁定すべき択一:
  - linux g1 を exact contract-hash で grandfather するか、detached acquisition evidence を新設するか。推奨は前者。
  - selector を proof-chain 入口として6種に含めるか、狭義の入口から除外して5種とするか。推奨は前者。
  - silo ability-probe writers を暫定対象にするか、真の promotion consumer を別途同定するまで「昇格入口」を未実装扱いにするか。推奨は後者。
  - receipt は zero-byte-impact の in-memory capability とするか、既存 bytes 不変を緩めて durable sidecar を設計するか。推奨はこの wave では in-memory。