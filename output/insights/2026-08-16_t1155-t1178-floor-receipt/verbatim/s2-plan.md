# 段 2 実装プラン

## (P1)〜(P5) の裁定

| 論点 | 選択 | 根拠 |
|---|---|---|
| P1 | 暫定案を採用 | artifact には絶対パス 2 項目を除いた射影と、raw `OracleReceipt.as_dict()` の canonical SHA-256 を載せる。raw receipt は private job staging に create-only で残す。 |
| P2 | 暫定案を採用 | `sort_best` では receipt key を必須、非 `sort_best` では key 自体を禁止する。`None` による擬似的な「不在」や `prepare_fn is prepare_cell` 分岐は使わない。 |
| P3 | 暫定案を採用し、両 JSONL を含む形へ具体化 | `campaign_run_id` で抽出した `ledger.jsonl` と `attempt-ledger.jsonl` の canonical 射影を一つの digest にする。共有ファイル全体の hash は採らない。 |
| P4 | 対抗案を採用 | 到達不能も必ず拒否するが、内容不一致とは別の `floor-admission-unverifiable` reason にする。再審査すべき場所を判別可能にする。 |
| P5 | 暫定案を採用 | `RESULT_SCHEMA` を v4、`MANIFEST_SCHEMA` を v3 に上げ、旧版を受理しない。実 floor artifact が 0 件で、編集対象 `.py` に bytes pin もないため移行分岐は不要。 |

P1 で `_portable_argv` は流用しない。`orchestrator/campaign/s8b_floor_campaign.py:2645-2682` は非空の argv 列だけを受け、置換対象も `${OUT_ROOT}`、`${CCBENCH_ROOT}`、`${FETCHCONTENT_BASE_DIR}` の既知 root に限定される。`compiler_realpath` は通常そのいずれにも属さず、scalar を一要素 argv に包んでも `/usr/...` が残る。また argv の表示用変換であり、oracle identity の意味論や可逆性を保証しない。

## A: SWO PASS receipt の durable binding

### 1. portable receipt 契約の新設

`orchestrator/campaign/s8b_sort_swo_receipt.py:new:1-end`

次の leaf module を新設する。

```python
PORTABLE_SORT_SWO_RECEIPT_SCHEMA = "s8b-sort-swo-pass-receipt/v1"

def project_sort_swo_pass_attempt(attempt: object) -> dict[str, object]: ...
def validate_portable_sort_swo_pass_receipt(value: object) -> dict[str, object]: ...
```

`project_sort_swo_pass_attempt` は以下を実施する。

- outer attempt を exact 7-key、nested `oracle_receipt` を `OracleReceipt.as_dict()` と同じ exact 12-key で検査する。
- `event == "sort-swo-oracle-attempt"`、`classification == "pass"`、`reason_code == "sort-swo-oracle-pass"` を固定する。
- outer の `oracle_contract_id`、`materialized_hole_sha256`、`proposal_sha256` と nested の対応値を完全一致させる。
- `sort_swo_oracle.py:1328-1338` の現行 contract、corpus、flags、TU template 定数と照合する。
- `receipt_sha256` は nested raw receipt 全体を、UTF-8、`ensure_ascii=False`、`sort_keys=True`、`separators=(",", ":")`、`allow_nan=False` で canonical 化した bytes の SHA-256 とする。
- portable 射影は次の exact key とし、ホストパス 2 項目を含めない。

```text
schema
classification
reason_code
oracle_contract_id
materialized_hole_sha256
proposal_sha256
corpus_id
corpus_version
compiler_version
compile_flags_sha256
tu_sha256
tu_template_sha256
dependency_config_sha256
receipt_sha256
```

`validate_portable_sort_swo_pass_receipt` は exact key、固定文字列、現行 oracle 定数、SHA-256 型を検査し、`compiler_realpath` と `dependency_root_realpath` の混入を明示拒否する。

`orchestrator/campaign/sort_swo_oracle.py:187-216,373-391,1681-1707` と `orchestrator/campaign/s1_direct_comparison.py:159-164,685-722` は生成元として変更しない。

### 2. PortableBuiltRecord の条件付き exact key

`orchestrator/campaign/s8b_binary_admission.py:34-60,232-330`

P2 の「非 sort_best には key 自体が無い」を守るため、既存 `PORTABLE_BUILT_KEYS` は common 12-key として据え置く。

```python
PORTABLE_SORT_BEST_BUILT_KEYS = (
    PORTABLE_BUILT_KEYS | {"sort_swo_oracle"}
)

def portable_built_keys_for(configuration_id: object) -> frozenset[str]:
    return (
        PORTABLE_SORT_BEST_BUILT_KEYS
        if configuration_id == "sort_best"
        else PORTABLE_BUILT_KEYS
    )
```

`validate_portable_binary_record` の冒頭で `configuration_id` に応じた exact key 集合を検査する。その後、

- `sort_best`: `sort_swo_oracle` が必須で、新 validator を通す。
- 非 `sort_best`: common key 集合との比較により `sort_swo_oracle` の存在を拒否する。

これにより、呼出し側が top-level exact 検査を忘れても central validator では迂回できない。

`PORTABLE_BUILT_KEYS` 参照面は、base set 自体を変えない場合でも条件付き集合へ対応させるため、指定された全 3 module と 2 test を更新する。

- `orchestrator/campaign/s8b_floor_campaign.py:272,2697,3429-3449`
- `orchestrator/campaign/s8b_floor_stats.py:915`
- `orchestrator/campaign/s8b_ratified_freeze.py:183,1653-1655`
- `orchestrator/tests/test_s8b_floor_campaign.py:6743-6745`
- `orchestrator/tests/test_s8b_binary_admission.py:118-121`

### 3. producer での取得、private 保存、portable 射影

`orchestrator/campaign/s8b_floor_campaign.py:163-165,1882-1912,2010-2038,2445-2449,2579-2598`

`_prepared_binding` 直後に、production/fake 共通で次を実行する。

```python
if configuration_id == "sort_best":
    if prepared.oracle_attempt is None:
        raise FloorCampaignError("sort_best SWO PASS receipt missing")
    sort_receipt = project_sort_swo_pass_attempt(prepared.oracle_attempt)
else:
    if prepared.oracle_attempt is not None:
        raise FloorCampaignError("non-sort cell carries SWO receipt")
```

`prepare_fn is prepare_cell` の条件には入れない。fake `prepare_fn` も同じ gate を通す。

production では必ず存在する `marker_root` に、既存 `_create_private_json` と同じ 0600、`O_EXCL`、fsync 契約で次を保存する。

```text
sort-swo-oracle-pass-<sha256(cell_id)[:16]>.json
```

内容は `{schema, cell_id, oracle_attempt, portable_receipt}` とする。絶対パスを含む raw attempt はここだけに置き、manifest、result、公開 journal には転記しない。fake で `marker_root` が未設定でも receipt 検査は省略せず、private file の生成だけを行わない。

`built[cell_id]` には `sort_best` の場合だけ `"sort_swo_oracle": sort_receipt` を追加する。

`orchestrator/campaign/s8b_floor_campaign.py:2685-2739,2742-2801`

- `_validate_portable_built` は `portable_built_keys_for` を使用する。
- `project_built_records` は `sort_swo_oracle` を canonical JSON copy し、raw attempt は参照しない。
- runtime key は静的な単一集合による緩い union にせず、`configuration_id`、stored/fresh、FetchContent 有無から exact set を返す `_runtime_built_keys_for(...)` に置換する。
- `_preflight_runtime_store_record` も同じ helper を使う。

### 4. manifest/result の coverage

`orchestrator/campaign/s8b_floor_campaign.py:2827-2863,4288-4311`

次の共通検査を追加し、manifest と result の組立前に通す。

```python
def _validate_binaries_cover_cells(
    binaries: Mapping, cells: Sequence[Mapping]
) -> None: ...
```

検査内容は以下とする。

- `cells` が非空で、`cell_id` が一意。
- 各 holdout に `sort_best` がちょうど 1 cell。
- `set(binaries) == {cell["cell_id"] for cell in cells}`。
- 各 binary record の `cell_id`、`holdout_id`、`configuration_id` が対応 cell と完全一致。

これにより、空 `binaries` や cell 丸ごとの欠落を producer 自身でも拒否する。

`orchestrator/campaign/s8b_floor_contract.py:317-363`

`enumerate_cells` の `configurations` 確定後、各 holdout 共通集合に `"sort_best"` が無ければ `FloorContractError` とする。実 freeze 由来のゼロ sort_best を campaign 開始前に止める。

## B: admission claim と ledger digest

### 1. result receipt の構造契約

`orchestrator/campaign/s8b_floor_contract.py:31-34,231-249`

schema を以下へ更新する。

```python
RESULT_SCHEMA = "s8b-floor-result/v4"
MANIFEST_SCHEMA = "s8b-floor-manifest/v3"
FLOOR_HOLDOUT_ADMISSION_SCHEMA = (
    "s8b-floor-holdout-admission-receipt/v1"
)
```

同じ leaf に次を追加する。

```python
def validate_floor_holdout_admission_receipt(
    value: object,
) -> dict[str, object]: ...
```

receipt の exact key は次とする。

```text
schema
campaign_run_id
run_relpath
mode
protocol_sha256
freeze_sha256
manifest_sha256
claim_identities
admission_row_count
attempt_row_count
ledger_projection_sha256
```

`claim_identities` は `{cell_id: claim_digest}` の非空 mapping とし、`admission_row_count == len(claim_identities)` を要求する。`run_relpath` は絶対 path、`.`、`..`、逆 slash を拒否する canonical POSIX relative path とする。

### 2. read-only ledger inspector

`orchestrator/campaign/s8b_holdout_admission.py:36-51,53-73,460-498,609-636,865-970,1333-1363,new after :1379`

public API と構造化例外を追加する。

```python
class FloorHoldoutEvidenceError(HoldoutAdmissionError):
    category: str  # "unverifiable" | "mismatch"
    reason: str

def inspect_floor_holdout_admission_evidence(
    *,
    repo_root: Path,
    protocol: Mapping[str, object],
    verified_freeze_document: Mapping[str, object],
    freeze_sha256: str,
    manifest_sha256: str,
    campaign_run_id: str,
    run_relpath: str,
    mode: str,
    cells: Sequence[Mapping[str, object]],
    schedule: Sequence[Mapping[str, object]],
    sessions: Sequence[Mapping[str, object]],
) -> dict[str, object]: ...
```

この関数は `shared_admission_root` だけを使い、`provision_shared_admission_root` を呼ばない。root、`claims/`、`consumed/`、lock、ledger の lstat と no-symlink 検査も read-only で行う。

claim identity は既存の一回性 identity と一致させる。

```python
claim_digest = _claim_digest(_key_fields(
    freeze_sha256=freeze_sha256,
    freeze_holdout_key=cell["holdout_id"],
    configuration_id=cell["configuration_id"],
    ccbench_pin=protocol["ccbench_pin"],
    env_tag=protocol["env_tag"],
    observation_role=OBSERVATION_ROLE_FLOOR_CAMPAIGN,
))
```

各 selected admission row について以下を要求する。

- expected cell ごとにちょうど 1 行で、余分、欠落、重複がない。
- schema、event、role、campaign、run path、mode、protocol、freeze、manifest、cell identity が一致する。
- `claims/<claim_digest>.claim` が canonical 1 JSON line として存在する。
- claim の exact shape、key、campaign、cell、workload、attempt IDs が schedule からの再導出値と一致する。

attempt row の期待集合は session から次のように導く。

- `probe_before.competing is True`: measure が呼ばれず、ticket は未消費なので row を期待しない。
- `probe_before.competing is False`: post-probe competing、launch failure、invalid result を含め、measure wrapper が ticket を先に消費するため row を必須とする。
- selected attempt row の集合を `(claim_digest, attempt_id)` で期待集合と完全一致させ、対応する `consumed/<claim_digest>-<sha256(attempt_id)>.json` が row と完全一致することも検査する。

### 3. P3 の canonical ledger digest

`ledger.jsonl` と `attempt-ledger.jsonl` は lock 内で既存 `_read_ledger` により全行を strict parse する。その後、各々から次だけを選ぶ。

```python
row.get("campaign_run_id") == campaign_run_id
```

選択した main 行は `(cell_id, claim_digest)`、attempt 行は `(cell_id, attempt_id, claim_digest)` で昇順にする。各 row は parse 済み dict をそのまま canonical 化する。

hash 入力は次の一つの canonical JSON object とする。

```python
projection = {
    "schema": "s8b-floor-admission-ledger-projection/v1",
    "campaign_run_id": campaign_run_id,
    "admission_rows": sorted_admission_rows,
    "attempt_rows": sorted_attempt_rows,
}
digest_input = json.dumps(
    projection,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
ledger_projection_sha256 = sha256(digest_input).hexdigest()
```

配列境界と schema domain separator があるため行連結の曖昧性はない。他 campaign の追記は抽出集合に入らず digest を変えない。同じ `campaign_run_id` の余分な行は coverage/重複検査で hash 前に拒否する。

`ledger.jsonl` は expected cells が非空なので、file 欠落または selected 0 行を必ず拒否する。`attempt-ledger.jsonl` の 0 行は、全 session が pre-probe competing で消費期待集合も 0 の場合だけ正しい。消費期待が 1 件以上なら欠落・0 行を拒否する。

### 4. result 発行と自己検査

`orchestrator/campaign/s8b_floor_campaign.py:4288-4431`

`assemble_result` に default 無しの必須引数を追加する。

```python
def assemble_result(
    *,
    ...,
    holdout_admission: Mapping,
) -> dict:
```

`validate_floor_holdout_admission_receipt` で正規化し、result の exact key `"holdout_admission"` に格納する。

`orchestrator/campaign/s8b_floor_campaign.py:5151-5175,5266-5313`

- `M-finalize-pending` では result staging より前に、既存 journal sessions から inspector を再実行する。
- fresh/resume 通常完走では `runner.run()` 後、`assemble_result` より前に inspector を実行する。
- inspector の receipt を `assemble_result` と自己検査の両方へ渡す。
- missing/mismatch の場合は result pending bytes を作らない。通常走では `terminal/artifact-invalid` に granular reason を残す。

manifest hash が確定してから admission row が作られ、その後 result が作られるため、hash 循環は発生しない。

### 5. pure verifier の責務

`orchestrator/campaign/s8b_floor_stats.py:593-665,785-796,880-950`

署名を次へ変更する。

```python
def verify_floor_artifact(
    artifact: Mapping,
    expected_protocol: Mapping,
    expected_binaries: Optional[Mapping] = None,
    *,
    expected_holdout_admission: Mapping,
    expected_use_perf: bool,
) -> list:
```

- `expected_holdout_admission` は必須 keyword-only とし、省略可能な bypass を作らない。
- artifact schema が result v4 であることを最初に検査する。
- artifact と expected の admission receipt を共有 validator で別々に正規化し、完全一致させる。
- expected receipt は live inspector 由来である、という trust boundary を docstring に明記する。
- 各 `expected_cells[holdout]` に `sort_best` がちょうど一つあることを、session 走査前に検査する。
- `_verify_binaries_section:897-901` の後方互換 skip を削除し、`binaries` が missing/空なら `expected_binaries is None` でも必ず問題を返す。
- binaries の expected/got set 差分 `:942-949` を維持する。

純関数は admission root へ触れない。root の欠落は呼出し側 inspector が拒否し、純関数は渡された live receipt と artifact receipt の構造・同値だけを担当する。

### 6. ratified closure と別 consumer

`orchestrator/campaign/s8b_ratified_freeze.py:145-180,197-203,258-263,1641-1747,1750-1758,2181-2247,2995-3046,3067-3116`

- `_RESULT_KEYS` に `holdout_admission` を追加する。
- manifest v3、result v4 のみ受理し、error message は schema 定数から作る。
- `_PORTABLE_BINARY_KEYS` の単一集合を廃し、conditional key helper を使う。
- `_validate_journal` 完了後、`_validate_result` より前に local import した admission inspector を呼ぶ。local import とするのは `s8b_holdout_admission.py:34` の現行逆向き import との循環を避けるため。
- `campaign_run_id` は official path parser の `run_id`、`run_relpath` は result path の親から先頭 `output/` を除いた値を外部期待値とする。
- inspector の expected receipt を `_validate_result`、さらに `verify_floor_artifact` へ渡す。
- binding graph に protocol、freeze、manifest、official run id、derived run relative path と receipt の各対応 edge を追加する。

例外分類は次とする。

- admission root、lock、ledger、claim が存在しない、または読めない: `RatifiedFreezeError(reason="floor-admission-unverifiable", cause=<granular reason>)`
- 行、claim、marker、digest、artifact receipt が不一致: `RatifiedFreezeError(reason="floor-admission-mismatch", cause=<granular reason>)`

`_RUN_BASENAMES:258-263` は変更しない。共有 root は run directory 外かつ他 campaign が追記するため、`ledger.jsonl` 全 bytes や `claims/` を G/H run artifact closure に加えると、無関係な追記だけで過去 closure が壊れる。既存 `result.json` が semantic receipt を capture し、live shared root は別の I/O 検査層で照合する。

`orchestrator/campaign/s8b_holdout_freeze.py:55-62,1275-1285,1310-1395`

- `FLOOR_RESULT_KEYS` に `holdout_admission` を追加する。
- result v4 を要求する。
- v1 freeze から full cells と schedule を再導出する。
- result sibling の `manifest.json` を nofollow で読み、bytes hash を独立取得して result の `manifest_sha256` と一致させる。
- official path から run id/run relative path を導き、inspector を呼ぶ。
- live receipt を `verify_floor_artifact` へ渡す。
- unreachable と mismatch を別 prefix の `FreezeError` として拒否する。

`orchestrator/campaign/s8b_oracle_report.py:1820-1848`

production code は変更不要である。既に `reverify_published_freeze` を report 生成前に呼び、`RatifiedFreezeError` で return code 2、出力未作成になるため、ratified 層の新拒否がそのまま report へ伝播する。

## 新設検査を通る正例

計画上の正例は次の一連とする。

```python
live_receipt = inspect_floor_holdout_admission_evidence(
    repo_root=repo_root,
    protocol=protocol,
    verified_freeze_document=freeze,
    freeze_sha256=freeze_sha256,
    manifest_sha256=manifest_sha256,
    campaign_run_id=run_dir.name,
    run_relpath=run_dir.relative_to(out_root).as_posix(),
    mode="official",
    cells=cells,
    schedule=schedule,
    sessions=journal_sessions,
)

result = assemble_result(
    ...,
    holdout_admission=live_receipt,
)

problems = verify_floor_artifact(
    result,
    expected_protocol,
    expected_binaries=journal_binary_receipts,
    expected_holdout_admission=live_receipt,
    expected_use_perf=True,
)
```

正例の admission root は、全 cell の main admission 行と claim file、`probe_before.competing is False` の全 session に対応する attempt 行と consumed marker を持つ。この場合だけ `problems == []` になるテストを追加する。

## 恒真化を防ぐ分岐

| 縮退入力 | 発火させる分岐 |
|---|---|
| 空 `binaries` | producer の `_validate_binaries_cover_cells` と、`s8b_floor_stats.py:897-904` の無条件 missing/empty 拒否 |
| cell 丸ごと欠落 | producer の binary/cell set 完全一致、stats の `:791-795` と `:942-949`、claim identity mapping の exact cell set |
| sort_best cell がゼロ | `s8b_floor_contract.py:350` 直後の freeze gate と、`verify_floor_artifact` の holdout ごとの `sort_best` 件数検査 |
| main ledger が 0 行 | inspector が `ledger.jsonl` の実在を先に要求し、selected main rows 数と非空 expected cells 数を hash 前に比較 |
| result の admission field 欠落 | result exact key gate、required `expected_holdout_admission`、receipt validator の三段で拒否 |
| attempt ledger が 0 行 | 消費期待が非空なら exact set 差分で拒否。全 pre-probe competing の場合だけ 0 行を正例として許す |

## 既存 fixture・meta test への波及

- `orchestrator/tests/test_s8b_floor_campaign.py:287-300,1268-1289,2987-3001`: fake `PreparedCell` は `sort_best` のときだけ deterministic raw PASS attempt を返す。
- 同 `:3330-3364`: resume schema test は v1/v2 の両旧版拒否へ変更する。空 cells/built を使う perf-preflight test は、stock と sort_best を含む最小 exact fixture へ置換する。
- 同 `:3387-3392`: `assemble_result` 直接呼出しに valid admission receipt を渡す。
- 同 `:5362-5383,8243-8267`: `verify_floor_artifact` 直接呼出しへ independent expected admission receipt を渡す。
- 同 `:6743-6750`: record exact key meta test を conditional helper に変更し、sort receipt が manifest/result で同一、raw absolute path が無いことも固定する。
- 同 `:6844-6897,6900-6925`: portable record helper に configuration 条件付き SWO receipt を追加する。
- 同 `:8225-8268`: 空 binaries、sort receipt 欠落、非 sort への余分 receipt、receipt 改竄を追加する。
- `orchestrator/tests/test_s8b_materialization.py:453-567`: golden fixture の `v1` 構成を `sort_best` にし、fake PASS receipt を与える。manifest v3 と receipt 増分に合わせ、production helperを使わない独立 canonical calculator で literal SHA を更新する。
- `orchestrator/tests/test_s8b_freeze_io.py:226-243,322-327`: `alt_a` を `sort_best` にし、fake prepare に receipt を追加する。
- `orchestrator/tests/test_s8b_ratified_freeze.py:398-410`: `_fixed_prepare` の sort cell に receipt を追加する。
- `orchestrator/tests/test_s8b_binary_admission.py:54-121`: helper に `configuration_id` を追加し、common key set と sort key set の両 meta assertion、必須/禁止の正負例を追加する。
- `orchestrator/tests/test_s8b_floor_contract.py:101-115`: result v4、manifest v3 の re-export と、sort_best 無し freeze の拒否を固定する。
- `orchestrator/tests/test_s8b_floor_stats.py:47-51,381-444`: wrapper が expected admission を必ず渡す。honest artifact に result v4、stock と sort_best を含む binaries、admission receipt を追加し、required keyword の meta testも追加する。
- `orchestrator/tests/test_s8b_holdout_admission.py:120-153`: manifest literal を v3 に更新する。inspector の正例、他 campaign 追記不変、main ledger 欠落、claim 改竄、attempt row/marker 欠落を追加する。
- `orchestrator/tests/s8b_v2_freeze_fixture.py:203-355`: binary builder に conditional SWO receipt、result builder に admission receiptを追加する。candidate repo 確定後の git common root に、独立 test-only canonical calculator で main/attempt/claim/consumed fixtureを置く。
- `orchestrator/tests/test_s8b_ratified_verify.py:277-325,420-436,502-510,529-570`: manual binaries、result exact keys、manifest schema、shared evidence fixtureを更新し、root unavailable と digest mismatch の reason を追加する。
- `orchestrator/tests/test_s8b_holdout_freeze.py:1271-end`: missing ledger、claim mismatch、digest mismatch の拒否を追加する。
- `orchestrator/tests/test_s8b_oracle_report.py:1444-1494`: admission root を到達不能にした official report が rc 2 かつ出力未作成になる伝播 test を追加する。

重複する fake receipt と admission filesystem は `orchestrator/tests/s8b_floor_evidence_fixture.py:new` に集約する。ただし期待 digest は production inspector を呼んで作らず、test-only canonical JSON 実装で独立計算し、恒真化を避ける。

## 段 5 の実装単位

brief §8 の A→B は安全だが、`s8b_floor_campaign.py`、`s8b_floor_stats.py`、`s8b_floor_contract.py` を二度所有するため、逐次差分の再衝突が大きい。次の三単位がよい。

1. U0 契約 spine、逐次先行

   `s8b_sort_swo_receipt.py`、`s8b_binary_admission.py`、`s8b_floor_contract.py`、`s8b_holdout_admission.py`、対応 unit tests、共有 test fixtureを所有する。schema、関数署名、digest 定義を先に固定する。

2. U1 producer

   `s8b_floor_campaign.py`、`test_s8b_floor_campaign.py`、`test_s8b_materialization.py`、`test_s8b_freeze_io.py` を所有し、A/B の発行側を一人で実装する。

3. U2 consumers

   `s8b_floor_stats.py`、`s8b_ratified_freeze.py`、`s8b_holdout_freeze.py`、`s8b_v2_freeze_fixture.py` と ratified/stats/freeze/report testsを所有する。

U0 完了後の U1 と U2 はファイル所有が素集合なので並行化できる。統合後に schema、fixture、全 consumer の受理集合を一度だけ acceptance 確認する。

## 変異事前登録候補

1. `s8b_floor_campaign.py:2445-2594` で `prepared.oracle_attempt` を読まず receipt key を落とす。  
   `test_s8b_floor_campaign.py::test_sort_best_swo_pass_receipt_reaches_manifest_and_result` が赤になるべき。

2. `s8b_sort_swo_receipt.py:new:project_sort_swo_pass_attempt` で絶対パスを射影へ残す、または `receipt_sha256` を sanitized 射影上で計算する。  
   `test_s8b_sort_swo_receipt.py::test_projection_omits_host_paths_and_hashes_full_raw_receipt` が赤になるべき。

3. `s8b_binary_admission.py:232-330` で sort receipt を `.get()` の optional 扱いにする。  
   `test_s8b_binary_admission.py::test_sort_best_requires_exact_swo_pass_receipt` が赤になるべき。

4. `s8b_floor_stats.py:897-904` に「binaries と expected_binaries が共に無ければ成功」を戻す。  
   `test_s8b_floor_stats.py::test_verify_rejects_empty_binaries_without_journal_receipts` が赤になるべき。

5. `s8b_holdout_admission.py:new:inspect_floor_holdout_admission_evidence` で `campaign_run_id` filter を除き、共有 file 全体を hash する。  
   `test_s8b_holdout_admission.py::test_inspection_digest_ignores_other_campaign_rows` が赤になるべき。

6. 同 inspector で `claims/<digest>.claim` の読取りまたは内容照合を省く。  
   `test_s8b_holdout_admission.py::test_inspection_rejects_tampered_claim_file` が赤になるべき。

7. 同 inspector で欠落した `ledger.jsonl` を `_read_ledger` の空列として受理する、または `provision_shared_admission_root` で補修する。  
   `test_s8b_holdout_admission.py::test_inspection_rejects_missing_main_ledger` が赤になるべき。

8. `s8b_ratified_freeze.py:3038-3046` で inspector 呼出しを削除する、または unavailable を skip する。  
   `test_s8b_ratified_verify.py::test_reverify_rejects_unreachable_admission_root` と `test_s8b_oracle_report.py::test_report_rejects_unverifiable_floor_admission` が赤になるべき。

本段では静的計画のみで、pytest は未実行である。

## 総括

採用した選択: P1・P2・P3・P5 は暫定案、P4 は fail-closed を維持したまま到達不能を別 reason にする対抗案を採用する。

最大のリスク: 別マシン審査で git-common-dir 側の admission root が搬送されていない場合、正しい成果物でも `floor-admission-unverifiable` になる。再検証環境の root 保全が運用上の前提となる。

段 5 の分割: 契約 spine U0 を先行し、その後 producer U1 と consumers U2 をファイル所有が素集合のまま並行実装する。