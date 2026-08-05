# T-478 設計案

結論は、**同じ `env_tag` の下に immutable な contract 世代列を保持し、現行解決と履歴解決を別 API にする案 (a)** を採るべきである。さらに、凍結 artifact を `contract_sha256` namespace に分離し、contract hash を campaign identity に含める必要がある。

調査は読み取り専用の静的検査だけで行った。pytest は実行しておらず、緑は主張しない。

## 親 brief の 9 件の再判定

静的再計算値は次のとおりだった。

- Pegasus contract: `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`
- linux-baremetal contract: `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7`
- floor protocol bytes: `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac`
- selector journal bytes: `d41135998cff3047cf792047239a3147a1154929e560b4a2e413e4ac14f9e000`
- calibration bytes: `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49`

| # | 判定 | 根拠・補足 |
|---:|---|---|
| 1 | 正しい | contract の canonical hash は `orchestrator/campaign/env_contract.py:145-160`、登録値は `:168-193`。 |
| 2 | 正しい | `output/s8b-freeze/floor_protocol.json:1` が `e576…` を内包し、`orchestrator/tests/test_frozen_artifacts.py:38-46,139-143` が 23 件・`261cec…` を固定する。 |
| 3 | 正しい | `output/s8b-freeze/selector-runs/journal.jsonl:1` に `protocol_sha256=261cec…`、journal 自体の pin は `test_frozen_artifacts.py:67-68`。 |
| 4 | 正しい | pre-oracle blob と worktree bytes の完全一致は `s8b_floor_campaign.py:1411-1416`。 |
| 5 | 正しい | current registry との完全一致および拒否は `s8b_floor_contract.py:104-151`。 |
| 6 | **件数が誤り** | resolver が `lookup()` のみなのは正しい (`env_contract.py:202-209`)。ただし executable な lookup call は **18 箇所**で、20 ではない。20 になるのは alias/import 束縛 `p3_s4_loop_trigger_gating.py:95`、`pegasus_floor_scoping.py:23` も callsite に数えた場合だけ。 |
| 7 | 正しい | 旧 protocol を残すと current validation が拒否し、書換えは seal/journal/pin を壊す。さらに writer 自体が固定 path・create-only (`s8b_floor_campaign.py:566-575`)。 |
| 8 | 正しい、ただし要限定 | 列挙されたフィールドは実在する。ただし origin ledger は現 tree では型・codec・identity 面 (`reflux_origin_ledger.py:235-258,384-425,450-462,1538-1558`) までで、current registry を解決する producer/consumer 接続は見つからない。既存の end-to-end binding としては未配線である。 |
| 9 | 正しい | prereg の `evidence_contract_sha256` は prereg evidence JSON の semantic hash (`s8c_preregistration.py:330-337,1182-1195`) であり別概念。 |

18 call は `loop.py:72`、`pipeline.py:535`、`p3_s4_loop_trigger_gating.py:324`、`pegasus_floor_scoping.py:75`、`s8b_floor_campaign.py:313,412,1874,2755`、`s8b_oracle_driver.py:762`、`s8b_oracle_report.py:1202`、`s8b_ratified_freeze.py:960,1803,2287,2880`、`silo_ladder_rung1.py:1932,3519,3737,4418` である。

## 1. 参照閉包の全件表

以下は raw occurrence 数ではなく、同じ義務を実装する call をまとめた**意味的 surface 47 行**である。18 lookup call は上記のとおり別に数えた。

- `(L)` live 照合
- `(P)` 永続記録
- `(G)` golden/pin
- `(N)` namespace

### Production

| ID | file:line | 分類 | 移行時の挙動 |
|---:|---|:---:|---|
| 01 | `orchestrator/campaign/env_contract.py:63-103,145-160,168-209` | G | path/SHA を替えると contract hash が変わる。現状は旧 contract の逆引きが消滅する。 |
| 02 | `orchestrator/campaign/env_attestation.py:643-692` | L | 渡された contract の path/SHA を厳密照合する。旧 contract と旧 file を保持すれば履歴照合可能だが、current lookup 経由では新 file だけを見る。 |
| 03 | `orchestrator/campaign/execution_guard.py:67-85,284-345` | P | 新 receipt は g2 hash/profile を焼き込む。旧 receipt は g1 のまま残る。 |
| 04 | `orchestrator/campaign/execution_guard.py:88-139` | L | 旧 receipt を g2 期待値で照合すると拒否。g1 contract/profile を渡せば完全一致を再計算できる。 |
| 05 | `orchestrator/campaign/loop.py:62-98` | L | Pegasus では contract object が current registry と完全一致しなければ拒否。旧 contract の current 実行は拒否される。 |
| 06 | `orchestrator/campaign/pipeline.py:532-543` | L | qualification は登録済み Pegasus contract の exact object だけを受理。g1 は g2 移行後に拒否される。 |
| 07 | `orchestrator/campaign/ident.py:2-10,130-156`; `loop.py:131-145` | N | **重大な欠落**。一般 campaign ID は env/contract を含まないため、同じ `pegasus` の g1/g2 が同じ WAL/layout に衝突する。 |
| 08 | `orchestrator/campaign/p3_s4_loop_trigger_gating.py:86-95,327-354,701-712` | N | P3 も identity に入れるのは `measurement_env="pegasus"` だけ。世代移行後も同じ ID になり、既存 layout は `allow_resume=False` により拒否される。 |
| 09 | `p3_s4_loop_trigger_gating.py:357-370,573-580` | P | provenance entry は contract hash と receipt を固定する。旧 entry は g1 のまま。 |
| 10 | `orchestrator/campaign/buildcache.py:635-670` | N | `contracts/<contract_sha256>/` が g2 namespace になる。旧 cache は残るが g2 は cache miss。破綻ではない。 |
| 11 | `buildcache.py:366-393,751-755` | P | cache manifest は g1/g2 を固定し、異世代再利用を拒否する。正しい fail-closed。 |
| 12 | `orchestrator/campaign/pegasus_floor_scoping.py:74-80` | L | scoping の照合対象が新 calibration へ追随する。旧値を現行値としては扱わない。 |
| 13 | `orchestrator/campaign/s8b_floor_contract.py:104-151` | L | 旧 protocol の `e576…` と current g2 が不一致になり拒否。proof chain の最初の実破断点。 |
| 14 | `orchestrator/campaign/s8b_approved.py:45-49` | G | `APPROVED_ENV_TAG="pegasus"` は世代を区別しない。builder は同じ tag から g2 hash を導出する。 |
| 15 | `orchestrator/campaign/s8b_floor_campaign.py:365-455` | P | builder 出力の contract hash と protocol bytes/SHA が変わる。旧 `261cec…` golden とは別物になる。 |
| 16 | `s8b_floor_campaign.py:138-149,566-603`; `tools/pegasus/floor_campaign.sh:880-904` | N | protocol path が固定かつ create-only。新 protocol を同じ場所へ作れず、上書きは禁止。 |
| 17 | `orchestrator/campaign/s8b_prediction_runner.py:98-101,1553-1570` | N | protocol/journal/predictions が固定 path。既存 predictions があるため新世代 seal を同じ namespace には作れない。 |
| 18 | `s8b_prediction_runner.py:1485-1506` | P | journal header は protocol SHA を固定する。新世代は新 journal が必要。 |
| 19 | `orchestrator/campaign/s8b_selector_freeze.py:51-55` | N | selector verifier が旧固定 predictions path を読む。世代別 path 解決が必要。 |
| 20 | `s8b_floor_campaign.py:1374-1438` | L | 旧 protocol/journal の相互 seal はそのままなら破綻しない。旧 bytes を変更すると HEAD blob 照合で拒否される。 |
| 21 | `s8b_floor_campaign.py:882-925,1003-1017,2750-2782` | L | current launch は g2 receipt/build namespace を要求。旧 receipt/build result は current launch で拒否される。 |
| 22 | `s8b_floor_campaign.py:2230-2247` | P | campaign journal に protocol SHA と execution receipt を固定。新世代は別 journal が必要。 |
| 23 | `s8b_floor_campaign.py:3167-3176` | N | run directory は protocol SHA prefix を持つため g1/g2 は自然に分離される。ここは破綻しない。 |
| 24 | `orchestrator/campaign/s8b_oracle_manifest.py:377-400,659-685,738-760` | P | manifest と campaign preimage に contract hash が固定される。旧 manifest は g1 のまま。 |
| 25 | `orchestrator/campaign/s8b_oracle_driver.py:737-803,1220-1228` | L | current 実走では旧 manifest/contract を拒否する。これは維持すべき現行 gate。 |
| 26 | `orchestrator/campaign/s8b_oracle_report.py:1189-1208,1361-1380` | L | report も current lookup を使うため、移行後は旧 manifest の履歴 report まで拒否する。履歴 resolver が必要。 |
| 27 | `orchestrator/campaign/s8b_ratified_freeze.py:61-85,2455-2623` | N | selector protocol/journal/predictions の path が g1 固定。g2 を同じ path へ置けない。 |
| 28 | `s8b_ratified_freeze.py:1795-1879,2272-2297,2870-2886` | L | journal、portable command、protocol full validation が current lookup を使う。旧 ratified proof の主な「解決不能」地点。 |
| 29 | `s8b_ratified_freeze.py:144-179,2969-3030` | P | protocol→receipt の hash 等式は旧 artifact 内で成立したまま。破断はこの等式ではなく、その前の current resolver。 |
| 30 | `orchestrator/campaign/silo_ladder_rung1.py:1928-1972,4417-4445` | P | 新 evidence は g2 path/SHA/contract hash を固定する。旧 evidence の書換えは禁止。 |
| 31 | `silo_ladder_rung1.py:1288-1302,1556-1710` | P | `validate_evidence` は artifact 内部の g1 binding/attestation を検査するため、旧 bytes は自己整合のまま。 |
| 32 | `silo_ladder_rung1.py:3496-3527,4817-4826` | L | public `verify-result` は current source bytes と current calibration を要求し、移行後の旧 evidence を拒否する。履歴 verify と current binding の分離が必要。 |
| 33 | `orchestrator/campaign/reflux_origin_ledger.py:235-258,384-425,450-462,1538-1558` | P | hash は manifest、origin ID、cell key に固定される。旧 ledger は自己整合だが、現状は hash→contract resolver がない。checked-in 実 instance は見つからない。 |
| 34 | `tools/pegasus/probes/t419_probe_causality.py:3388-3418` | L | 新 registry へ追随する。旧 submission SHA を渡せば新 SHA と不一致になり拒否される。 |

### Artifact、test、docs

| ID | file:line | 分類 | 移行時の挙動 |
|---:|---|:---:|---|
| 35 | `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440-1493,1599-1603,1685-1690` | P | g1 calibration 本体。削除すると g1 の履歴検証が本当に解決不能になるため永続保持が必要。 |
| 36 | `output/env/pegasus/calibration/attempts/0_867876.nqsv/final-receipt.json:7-11`; `publish.json:1-4`; `job-staging/0:867876.nqsv/calibrate.stdout:9-14` | P | g1 取得・publish の履歴。値は静かに古いままで正しい。 |
| 37 | `output/s8b-freeze/floor_protocol.json:1` | P | `e576…` を固定。bytes は不変でなければならない。current validation からは外れる。 |
| 38 | `output/s8b-freeze/selector-runs/journal.jsonl:1`; `selector_predictions.json:1-27` | P | `261cec…` と pre-oracle source を固定。旧 protocol と一緒なら破綻しない。 |
| 39 | `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:8-20,567-570,4133-4554` | P | g1 path/SHA/contract と raw-bundle closure を固定。current eligibility は失うが履歴 integrity は保持できる。 |
| 40 | `.../raw-bundle-attempt-1/campaign-identity-receipt.json:182-186`; `attempts/1/submit-receipt.json:214-218` | P | silo の source commit `8b3d50e…` を固定。履歴 source binding はこの commit の blob と照合できる。 |
| 41 | `output/env/pegasus/t419-probe-causality/0_888740.nqsv/manifest.json:67-70,95-118`; 同 `0_889279:70-73,98-121`; `0_889310:71-74,99-122`; `0_889400:72-75,100-123` と各 `result.json` | P | g1 path/SHA を記録した実験履歴。静かに旧値のまま。certified proof chain には昇格しない。 |
| 42 | `orchestrator/tests/test_env_contract.py:46-63,239-251,431-472,678-691` | G | lookup literal、既知自己不整合、contract SHA golden が g2 移行で赤になる。g1 golden は消さず履歴 test に変える。 |
| 43 | `orchestrator/tests/test_frozen_artifacts.py:38-85,87-149` | G | g1 protocol/journal と exact 23 件を固定。**更新せず維持**し、新世代 manifest を別に足す。 |
| 44 | `orchestrator/tests/test_s8b_protocol_builder.py:108-118,401-418` | G | approved Pegasus builder の `261cec…` pin が current g2 では赤。g1 historical と g2 current を別 test にする。 |
| 45 | `orchestrator/tests/test_s8b_floor_campaign.py:3231-3243,3283-3443` | G | real seal が g1 protocol/contract と current lookup を同時に要求するため赤。履歴 resolver test へ移す。 |
| 46 | `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1172-1229` | G | committed silo evidence と current registry の結合が赤。historical integrity と current g2 evidence の二本へ分離する。 |
| 47 | `test_env_attestation.py:275-368`; `test_execution_guard.py:55-113,192-219`; `test_campaign.py:1986-1998,2417-2418`; `test_p3_s4_loop_trigger_gating.py:675`; `test_s8b_oracle_driver.py:1155-1156,4108-4136`; `test_s8b_oracle_report.py:1916-1971`; `test_silo_ladder_rung1_driver.py:803,1154-1165`; `test_s8b_freeze_io.py:244-276`; `test_s8b_ratified_freeze.py:288-437` | L | literal g1 pin ではなく、その時点の lookup から fixture を作る群。値は g2 に追随し通常は破綻しないが、履歴/current API の取り違えを撃つ test へ強化する。 |

現行運用文書の literal は `docs/pegasus-runbook.md:477-509,519-525` にあり、移行後は g2 current と g1 history を併記する必要がある。`docs/decisions.md:3305-3309` と `docs/failures.md:2180-2194` は歴史記録なので旧値を変更しない。

### 明示的な除外

| file:line | 除外理由 |
|---|---|
| `orchestrator/campaign/s8c_preregistration.py:69-84,330-337,1182-1195`; `s8c_preregistration_evidence_contract.v1.json:1-39,454` | `evidence_contract_sha256` は prereg evidence document の semantic hash。env contract ではない。 |
| `tools/pegasus/probes/t419_probe_causality.py:3380-3385,3532-3534` | `env_contract_sha256` は `env_contract.py` **source file の bytes hash**。`ExecutionEnvironmentContract.contract_sha256` ではない。 |
| `tools/pegasus/t126_qualification.sh:615,706`; `submit_t126_qualification.sh:763` | `protocol_sha256` は T126 qualification control protocol。s8b floor protocol ではない。 |
| `test_buildcache_v2.py:136,334-348,736`; `test_s8b_floor_contract.py:31-49`; `test_reflux_origin_ledger.py:88-134`; `test_s8b_oracle_manifest.py:114-382` | 同じ概念を試す synthetic hash だが、`REGISTRY["pegasus"]` を参照しない。実移行では値が変わらない。 |
| `output/insights/**`、`docs/archive/**` | 検出された `e576…` 等は調査記録・mutation log・逐語。例: `output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:155-180`、`docs/archive/worklog-phase3-0722-0724.md:148-192`。certified selector が読む artifact ではない。 |
| `docs/decisions.md:3305-3309`, `docs/failures.md:2180-2194` | 旧世代の正しい歴史記述。current pin として更新せず保存する。 |

## 2. 世代機構の設計択一

### 案 A — env_tag ごとの immutable 世代列 + hash 逆引き（推奨）

実装面は `orchestrator/campaign/env_contract.py:63-103,163-209`。

型・API の骨格は次とする。

```python
@dataclass(frozen=True)
class ContractGeneration:
    generation: int
    contract: ExecutionEnvironmentContract
    lifecycle: Literal["pending", "current", "historical"]

@dataclass(frozen=True)
class ResolvedContract:
    generation: int
    contract: ExecutionEnvironmentContract
    is_current: bool

GENERATIONS: Mapping[str, tuple[ContractGeneration, ...]]
REGISTRY: Mapping[str, ExecutionEnvironmentContract]  # current view only

def lookup(env_tag: str) -> ExecutionEnvironmentContract: ...

def resolve_by_contract_sha256(
    contract_sha256: str,
    *,
    expected_env_tag: str | None = None,
) -> ResolvedContract: ...

def require_current(
    env_tag: str,
    contract_sha256: str,
) -> ExecutionEnvironmentContract: ...
```

構築時に以下を fail-closed 検査する。

- generation は正整数・単調増加・重複なし。
- contract hash は全 env を通じて一意。
- 各 `env_tag` に current はちょうど一つ。
- `contract.env_tag` と registry key は完全一致。
- 全世代の calibration path が存在し、bytes SHA が一致する。
- `pending` は `lookup()` や current launch から解決できない。

凍結 artifact は新規に次の namespace へ置く。

```text
output/s8b-freeze/contracts/<contract_sha256>/
  bundle.json
  floor_protocol.json
  selector_predictions.json
  selector-runs/...
```

`bundle.json` は generation、env_tag、contract SHA、calibration ref、protocol ref、selector 全 file の path/SHA を exact-set で持つ。g1 bundle は旧 legacy path を**外側から参照**し、旧 bytes は編集しない。

実装位置:

- current/history validator 分離: `s8b_floor_contract.py:104-151`、`s8b_floor_campaign.py:308-324`
- bundle path 解決: `s8b_floor_campaign.py:138-149`
- selector namespace: `s8b_prediction_runner.py:98-101`、`s8b_selector_freeze.py:51-55`
- historical proof: `s8b_ratified_freeze.py:1795-1879,2272-2297,2870-2886`
- historical report: `s8b_oracle_report.py:1189-1208`
- silo history/current 分離: `silo_ladder_rung1.py:3496-3527,4817-4826`
- campaign identity: `ident.py:28-44,130-156`、`loop.py:131-145`、`p3_s4_loop_trigger_gating.py:327-334`

API は意図を名前で分離する。

```python
validate_protocol_current(document)       # lookup + require_current
verify_protocol_history(document)         # hash reverse resolution

verify_silo_history(document, raw_bundle)
validate_silo_current_bindings(document, repo)
```

boolean の `allow_historical=True` は設けない。current launcher、oracle driver、certified selector は必ず `require_current()` を使う。

旧 artifact の保証:

- floor: protocol の g1 hashから g1 contract/calibrationを逆引きし、selector journal・receipt・ratified equality chainを再計算する。
- silo: `validate_evidence`、raw bundle、g1 contract を検証し、source bytes は raw bundle の `source_commit` (`campaign-identity-receipt.json:186`) の git blob SHA と binding SHA を比較する。
- origin ledger: `environment_contract_sha256` を一意な reverse index で解決する。旧 format に env_tag がなくても hash 一意性で解決可能。
- g1 calibration と、その source commit/git object を retention 対象にする。

受理集合を広げない機構:

1. current producer/launcher は artifact 宣言世代を信じず、`lookup(env_tag)` から current hash を導出する。
2. history resolver は検証・表示専用で、測定、receipt 発行、certified 選択 API から呼べない。
3. current eligibility は `artifact.contract_sha256 == lookup(env_tag).contract_sha256` を追加条件にする。
4. campaign identity に `environment_contract_sha256` を含める。同じ `pegasus` の g1/g2 は別 WAL/layout になる。
5. 一つの campaign、origin batch、selector proof 内の contract hash は単一値完全一致を要求する。origin ledger の cell-key 分離だけに依存しない。
6. attestation、self-comparison、receipt 完全一致は現状のまま維持する。

恒真化を撃つ変異:

- g1 を reverse index から削除 → g1 protocol/silo history test が失敗。
- resolver が要求 hash を無視して current を返す → g1 receipt/protocol hash test が失敗。
- current gate が任意の登録世代を許す → g1 artifact の current-launch refusal test が失敗。
- campaign preimage から contract hash を削除 → g1/g2 campaign ID 差分 test が失敗。
- artifact の generation number だけを変更 → bundleの contract/path/SHA完全一致 test が失敗。
- g1 origin/silo receipt を g2 campaign へ混入 → single-contract closure test が失敗。
- g1 calibration bytes を変更・削除 → all-generation calibration retention test が失敗。
- old proof verifierを current lookup に戻す → `e576…` replay test が失敗。

### 案 B — artifact に generation tag/manifest を持たせる

実装位置は `s8b_floor_contract.py:39,104-151` の protocol schema、`s8b_ratified_freeze.py:96-104` の generation schema、各 receipt/manifest。

骨格:

```python
@dataclass(frozen=True)
class DeclaredContractGeneration:
    env_tag: str
    contract_generation: int
    contract_sha256: str
    generation_manifest_sha256: str

def resolve_declared_generation(value: DeclaredContractGeneration) -> ResolvedContract: ...
```

既存の holdout `generation_number` (`s8b_ratified_freeze.py:100-103`) と同名にせず、`contract_generation` とする。

旧 bytes には新 field を追加できないため、`protocol_sha256=261cec… → g1 manifest` の外部 legacy mapping が不可欠になる。したがって結局 hash reverse resolver は必要であり、A より権威面が二重になる。

受理集合を広げないため、current launch は artifact の自己申告 generation を使わず、宣言 hashと current hash の両方を照合する。変異は generation number のみ変更、manifest 差替え、current check 除去を撃つ。

**採らない理由:** 自己申告世代を trust boundary に増やし、旧 artifact 対応には A の逆引きも必要になる。A の補助 metadata として bundle に generation を持つのはよいが、解決権威にはしない。

### 案 C — `pegasus-g2` という新 env_tag を切る

実装位置:

- 新 entry: `env_contract.py:168-194`
- site mapping: `p3_s4_loop_trigger_gating.py:88-95`
- approved pin: `s8b_approved.py:45-49`
- hard-coded Pegasus consumers: `silo_ladder_rung1.py:1932,3519,3737,4418`
- T419 probe: `t419_probe_causality.py:3394-3410`
- goldens: `test_env_contract.py:239-251,678-691`

旧 protocol の `env_tag="pegasus"` は自然に g1 を解決でき、新 evidence は `pegasus-g2` へ束縛できる。

ただし、旧 `pegasus` tag を current 実行可能のまま残すと「古い環境証拠を新 campaign に使う」穴になる。`pegasus` を `historical_only`、`pegasus-g2` を current とする lifecycle gate が別途必要で、結局世代管理を別名で実装することになる。

また一般 campaign identity は env を含まない (`ident.py:6-7`) ため、この案でも identity 修正は必要。hard-coded `pegasus` が一箇所残る変異を全 consumer inventory test で撃つ。

**採らない理由:** 同じ物理環境の較正更新ごとに env tag が増殖し、environment identity と calibration generation を混同する。origin ledger の hash-only 解決も別途必要。

### 案 D — 移行せず旧証拠を失格にし、新 protocol を凍結

current eligibility だけを考えれば、registry を g2 に替え、`s8b_floor_campaign.py:365-455` から新 protocol を作る案である。

しかし旧 protocol は `s8b_floor_contract.py:139-151`、旧 ratified proof は `s8b_ratified_freeze.py:1803-1879,2878-2886`、旧 oracle report は `s8b_oracle_report.py:1202-1207` で解決不能になる。P3 を満たさない。

**却下する。** 「parse できれば verify 済み」と定義を弱めることや、旧 hash mismatch を許すことも正しさゲートの緩和なので却下する。

## 3. 移行手順

[T-452] の順序は `README.md:141-166`、親 U-8 は `brief.md:11-17` にある。authority commit の後、campaign を閉じたまま U-2 と pin closure を隣接 2 commit にする。

| 段階 | 変更 | 期待する赤・判定 | 閉鎖区間・巻戻し |
|---|---|---|---|
| 0. 封鎖 | certified selector、floor/oracle campaign、silo promotion を停止。g1 hashes と 47 surface inventory を記録。 | 既存 test の赤は期待しない。赤があれば移行前故障として停止。 | ここから段 4 完了まで campaign を開かない。変更なし。 |
| 1. authority commit | `env_contract.py` に generations/reverse resolver/current gate。floor/report/ratified/silo を history/current API に分離。`ident.py`、`loop.py`、P3 identity に contract hash を追加。generation bundle schema/test を追加。current は g1 のまま。 | 実装前には `g1 resolves`、`current rejects history`、`g1/g2 campaign IDs differ`、`g1 proof replay` の新 test が赤であるべき。実装後の緑は親実測対象。 | artifact bytes は変えない。途中停止は authority commit 全体を revert すれば現挙動へ戻る。 |
| 2. U-2 commit（連続 2 commit の第1） | 新 calibration・取得 receipt を追加。g2 を `pending` 世代として登録。g2 floor protocol を `contracts/<g2-hash>/` に作り、この commit を selector の `pre_oracle_head` anchor にする。`lookup("pegasus")` はまだ g1。 | 正しい pending staging なら既存 suite を赤にしない。`pending generation is not current` test が、誤って lookup/current launch に露出した場合に赤となる。current を早期反転すると `test_env_contract.py:239-251,436-463,678-691`、`test_s8b_floor_campaign.py:3231-3443` が赤になるので停止。 | campaign は閉鎖継続。途中停止しても current は g1、追加 artifact は inert。commit を revert すれば完全に戻る。 |
| 3. pin closure commit（直後の第2） | 段2 HEAD を起点に g2 selector journal/predictions を生成。g2 bundle、silo evidence、必要な origin ledger を追加。g1 FROZEN_MANIFEST は変更せず、別 generation manifest/golden を追加。最後に current pointer を g2 へ反転し、runbook/current goldens/既知例外を更新。 | bundle 完成前は新 `current generation has complete pin closure` test が赤。pointer だけ先に反転すると env goldens、approved protocol pin (`test_s8b_protocol_builder.py:108-118`)、real seal、silo current binding が赤になる。g1 `test_frozen_artifacts.py:38-149` が赤になる変更は期待外であり、旧 bytes 改変として停止。 | pointer 反転は論理的に最後。作業途中は campaign を開かない。commit 後に問題があれば commit 全体を revert し、g1 current + pending g2 へ戻す。 |
| 4. closure 検査 | 親が計算ノードで関連 test/mutation を実測。全 g1 history replay、g2 current gate、mixed-generation refusal、frozen pins、docs checker を確認。 | 期待する赤はないが、本調査では緑を主張しない。特に g1 current-launch refusal は「拒否が成功」である。 | 全検査完了まで閉鎖。失敗時は段3を revert し、段2 pending 状態で修正する。 |
| 5. 再開 | g2 bundle hash を明示して campaign/certified selector を開く。 | 起動前 sentinel が `lookup("pegasus") == bundle.contract_sha256` と全 pin closure を再確認する。 | g1 は history-only のまま。g1 への自動 fallback はしない。 |

段2で g2 protocol を同時に置く理由は、selector runner が `pre_oracle_head` の committed protocol bytes と再導出 bytes の一致を要求するためである (`s8b_prediction_runner.py:1548-1570`)。protocol と selector evidence を同一 commit に押し込むと、正しい anchor commit が存在せず、U-8 の 2 commit 制約を満たせない。

## 4. 「解決不能」の定義

親 P3 の「現行コードで verify 可能、current eligibility は不要」という方向は正しいが、**verify の意味が不足している**。schema parse や内部 hash 一致だけを verify と呼べてしまう。

次の三状態を別結果として定義すべきである。

1. `integrity_resolved`
   - artifact の contract hash が一意な immutable contract に解決する。
   - contract の calibration path が存在し、bytes SHA・schema・cross-field が一致する。
   - protocol、journal、receipt、manifest、raw bundle、source commit の全参照が解決する。

2. `historically_verified`
   - `integrity_resolved` に加え、artifact が宣言する versioned predicate で proof chain を最後まで再計算できる。
   - 結果は pass/fail のどちらでもよい。旧 calibration が新 policy では失格でも、構成要素を解決して「historical integrity pass / current policy fail」と報告できれば解決不能ではない。

3. `current_eligible`
   - `historically_verified` に加え、contract hash が `lookup(env_tag)` の current hash と一致し、現行 attestation/self-comparison/approval/certified gate をすべて通る。

したがって「解決不能」は次のいずれかである。

- hash から contract を一意に得られない。
- calibration bytes、source commit/git blob、または参照 artifact が不在・hash mismatch。
- versioned verifier/predicate を実行できない。
- proof-chain の辺を再計算できず、単に記録値同士を比較するだけになる。

実際の破断点は次のとおり。

| proof chain | 現在壊れる地点 |
|---|---|
| g1 floor protocol → g1 contract | `s8b_floor_contract.py:139-151` が current g2 と比較して拒否。 |
| protocol → selector journal | journal の `protocol_sha256` 自体は成立したまま (`journal.jsonl:1`)。その前の protocol 解決で止まる。 |
| protocol/receipt → ratified freeze | `s8b_ratified_freeze.py:1803-1809,1869-1879` が current contract/calibration を使い拒否。 |
| protocol → portable run command | `s8b_ratified_freeze.py:2286-2297` が current clocks/numactl を使う。較正だけの変更なら偶然同値でも、権威として誤っている。 |
| full floor proof | `s8b_ratified_freeze.py:2878-2886` が equality chain `:2969-3030` に到達する前に拒否。 |
| oracle manifest → report | `s8b_oracle_report.py:1202-1207` が current contract 不一致として拒否。 |
| silo evidence → public verify | 内部検査は可能だが、`silo_ladder_rung1.py:3519-3527,4817-4826` の current-binding で拒否。 |
| origin ledger → contract | hash は identity に残る (`reflux_origin_ledger.py:450-462`) が逆引き API がなく、意味的 contract/calibration を復元できない。 |

## ユーザー裁定へ返す択一

1. 世代機構: A / B / C / D。推奨は A。D は P3 違反で却下。
2. P3 の verify 定義: parse/internal consistency の弱い定義か、上記三状態の強い定義か。推奨は強い定義。
3. D13 の改訂: env 値一般は identity に含めないまま、**contract-bound campaign だけ `environment_contract_sha256` を必須 preimage にする**か。推奨は改訂。現状維持は g1/g2 WAL 混在穴を残すため不可。

## 5. 本設計が保証しない範囲

- g1 evidence を g2/current eligibility に戻すこと。
- 旧 calibration が新 policy authority や新 self-comparison を満たすこと。
- 歴史的に「certified」と記録された結論の科学的妥当性を再承認すること。
- scheduler、物理 node、当時の負荷状態、消失した外部環境の再現。
- g1 build cache の g2 再利用。g2 cache miss は正しい。
- T419 probe manifests/results を certified proof chain に昇格すること。
- checked-in 実 instance がない origin ledger の過去 artifact の存在・完全性。
- 古い calibration fileやgit objectが将来削除された場合の復元。retention を破れば明示的に `unresolved` となる。
- producer provenance/content-addressed path 問題。これは [T-452 §7 `README.md:191-201`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t478-calibration-contract-generation/output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:191>) の別課題である。
- 旧凍結 bytes の更新、attestation/self-comparison/equality gate の緩和、mixed-generation fallback は一切保証・許可しない。

## 総括

- 推奨: 案 A（immutable 世代列 + hash 逆引き + current/history API 分離 + contract-hash namespace）。
- 参照閉包: 47 semantic surface、うち executable `lookup` call は 18。
- 親 brief の誤り: #6 の「20 callsites」のみ。正しくは18（alias/importを含めれば20）。
- #8 origin ledger は field/identity 面では正しいが、current registry との end-to-end 配線は未実装。
- P3 は三状態 `integrity_resolved / historically_verified / current_eligible` へ強化する。
- ユーザー裁定へ返す択一は 3 件。