# [T-419] U-2 contract generation 実装プラン

以下の行番号は変更前の現行 worktree を指す。実装・編集・pytest 実走は行わず、静的読解だけに基づく。

## 1. 設計方針

本 wave では、現行 g1 を一切変更せず次の層だけを追加する。

- `ExecutionEnvironmentContract` は hash 対象の値型としてそのまま残す。
- 全世代を低権限で表す `HistoricalContract` と、現行 production に渡せる `CurrentContract` を、継承関係のない wrapper として導入する。
- `GENERATIONS` は全世代、`REGISTRY` はそこから導出した current view とする。
- `lookup()` は削除する。current は `require_current()`、hash からの履歴解決は `resolve_by_contract_sha256()` に完全分離する。
- 現在は全 env が g1 だけなので、各世代列の末尾を current とする。ただし独立 golden 検査で g2 の無断追加を拒否する。将来の activation 機構を本 wave で先取りしない。
- `HistoricalContract` は「hash から immutable contract を解決した」という低権限 view であり、§5 の `historically_verified` 完了を意味しない。`CurrentContract` も current identity の必要条件であって、attestation 等を通った `current_eligible` の十分条件ではない。

## 2. `env_contract.py` の改造

### 2.1 hash 対象は固定

`orchestrator/campaign/env_contract.py:82-160` の `ExecutionEnvironmentContract`、全 field、`_canonical_obj()`、`contract_sha256` は変更しない。世代番号・lifecycle・current flag・wrapper authority をこの dataclass に追加してはならない。

### 2.2 型と API の配置・シグネチャ

`orchestrator/campaign/env_contract.py:160-163`、すなわち `contract_sha256` の直後かつ `_build_registry()` の直前へ、次の形を置く。

```python
@dataclass(frozen=True)
class HistoricalContract:
    generation: int
    contract: ExecutionEnvironmentContract

    @property
    def contract_sha256(self) -> str: ...


@dataclass(frozen=True)
class CurrentContract:
    generation: int
    contract: ExecutionEnvironmentContract

    @property
    def contract_sha256(self) -> str: ...


def is_valid_successor(
    predecessor: ExecutionEnvironmentContract,
    successor: ExecutionEnvironmentContract,
) -> bool: ...
```

実装条件は次のとおり。

- 2 wrapper は互いにも `ExecutionEnvironmentContract` にも継承させない。
- `generation` は bool を除く正整数、`contract` は exact `ExecutionEnvironmentContract` とする。
- consumer の既存 field accessを保つ場合も `__getattr__` ではなく、`env_tag`、`clocks_per_us`、`numactl`、`attestation_mode`、`isolation_policy`、`calibration_ref`、`contract_sha256` の明示的な read-only property だけを委譲する。
- `contract_sha256` は必ず `self.contract.contract_sha256` を返す。wrapper 自身を `asdict()` して再計算しない。
- production 境界では `type(value) is CurrentContract` を検査し、`isinstance(..., ExecutionEnvironmentContract)` や wrapper 共通基底への検査に緩めない。

transition predicate は `_canonical_obj()` 同士の leaf-level JSON Pointer 差分を取り、差分が非空かつ次の集合の部分集合である場合だけ真にする。

```python
frozenset({
    "/calibration_ref/path",
    "/calibration_ref/sha256",
})
```

これにより `/env_tag`、`/clocks_per_us`、`/numactl`、`/attestation_mode`、`/isolation_policy/*` は完全一致となる。`calibration_ref` object 全体を丸ごと除外して比較する実装は、将来 field が増えた場合に暗黙で可変化するため採用しない。

### 2.3 世代列と current view

`orchestrator/campaign/env_contract.py:163-194` の `_build_registry()` は名前を維持し、返り値だけを次の形へ変更する。

```python
dict[str, tuple[HistoricalContract, ...]]
```

宣言形は概念的に次とする。

```python
{
    "linux-baremetal": (
        HistoricalContract(generation=1, contract=<現行と同値の g1>),
    ),
    "pegasus": (
        HistoricalContract(generation=1, contract=<現行と同値の g1>),
    ),
}
```

既存の env 固有 literal と calibration pin は `orchestrator/campaign/env_contract.py:169-193` の値をそのまま移し、変更しない。

`orchestrator/campaign/env_contract.py:197-209` は次の初期化・API 群へ置き換える。

```python
GENERATIONS: Mapping[str, tuple[HistoricalContract, ...]]
REGISTRY: Mapping[str, CurrentContract]

def resolve_by_contract_sha256(
    contract_sha256: str,
    *,
    expected_env_tag: str | None = None,
) -> HistoricalContract: ...

def require_current(
    env_tag: str,
    *,
    contract_sha256: str | None = None,
) -> CurrentContract: ...
```

初期化時に fail-closed で検査する性質は次のとおり。

- 各 key の世代列は exact tuple かつ非空。
- `generation` は各 env 内で `1..N` の連番。
- registry key と内包 contract の `env_tag` は一致。
- `contract_sha256` は全 env・全世代を通じて一意。
- 隣接世代は必ず `is_valid_successor()` を満たす。
- `GENERATIONS` と hash reverse index は `MappingProxyType` で公開し、生の backing dict を module 属性に残さない。
- `REGISTRY` は各列の末尾と同じ contract/generation を `CurrentContract` で包んだ導出 view とし、別の literal 定義を持たない。

`resolve_by_contract_sha256()` は malformed/未知/非一意 hash と `expected_env_tag` 不一致を `EnvContractError` にする。current hashを渡しても返り値は低権限の `HistoricalContract` とする。

`require_current()` の `contract_sha256` は、artifact が hash を持つ consumer 用の追加照合であり、省略しても historical を許可する意味にはならない。常に `CurrentContract` だけを返す。

### 2.4 `lookup()` の扱い

`orchestrator/campaign/env_contract.py:202-209` の `lookup()` は削除する。

残すと `require_current()` と意味が重複し、将来 consumer が旧 API に戻る抜け道になる。後方互換 alias も設けない。production・test の全呼び出しを移行したうえで、current/history の解決経路を次の2本に限定する。

- current production: `require_current(...) -> CurrentContract`
- hash-bound history: `resolve_by_contract_sha256(...) -> HistoricalContract`

## 3. g1 の `contract_sha256` が byte 同一である論証

現行 hash preimage は `orchestrator/campaign/env_contract.py:145-160` だけで決まる。

1. `_canonical_obj()` は `asdict(self)` をそのまま返す。
2. `asdict()` は `IsolationPolicy` と `CalibrationRef` を再帰的な dict にし、`numactl` の tuple は tuple のまま保持する。
3. `json.dumps()` はその tuple を JSON array にし、`sort_keys=True`、`separators=(",", ":")`、`ensure_ascii=True` で canonical string を作る。
4. UTF-8 bytes にして SHA-256 を取る。

提案では `ExecutionEnvironmentContract` の6 field、nested dataclass、型、値を変更せず、現行 `orchestrator/campaign/env_contract.py:169-193` の constructor を wrapper/tuple の内側へ移すだけである。generation と wrapper field は `_canonical_obj()` の receiver に含まれない。したがって canonical object、canonical JSON string、UTF-8 bytes が現行と同一になり、g1 hash も同一になる。

特に次の既存 golden は変更禁止である。

- linux-baremetal: `orchestrator/tests/test_env_contract.py:714-727`
- pegasus: `orchestrator/tests/test_env_contract.py:730-743`
- 小 contract: `orchestrator/tests/test_env_contract.py:691-711`

generation/lifecycle を `ExecutionEnvironmentContract` に追加する案、wrapper を hash receiver にする案、`asdict(wrapper)` を使う案は byte 同一性を壊すため却下する。

## 4. consumer 移行表

静的検索では executable な呼び出しは21箇所・11 fileだった。brief の列挙にある `env_attestation.py` は `lookup()` caller ではなく型 consumer であり、逆に `loop.py` と T-419 probe が実 caller である。

| # | production 箇所 | 移行 | 理由 |
|---:|---|---|---|
| 1 | `tools/pegasus/probes/t419_probe_causality.py:3396` | `require_current()` | probe 入力として現行登録 calibration を読む。probe 方式自体は変更しない。 |
| 2 | `orchestrator/qualification/t126_driver.py:496` | `require_current()` | live qualification member の build/measurement 入口。 |
| 3 | `orchestrator/qualification/t126_driver.py:868` | `require_current()` | T-126 live run の環境 admission。control bytes は変更しない。 |
| 4 | `orchestrator/campaign/s8b_floor_campaign.py:313` | `require_current()` | current protocol validator へ current hash を供給する callback。 |
| 5 | `orchestrator/campaign/s8b_floor_campaign.py:412` | `require_current()` | 新しい floor protocol を組み立てる producer。 |
| 6 | `orchestrator/campaign/s8b_floor_campaign.py:1874` | `require_current(..., contract_sha256=protocol["contract_sha256"])` | live session command を current contract から再構築する。 |
| 7 | `orchestrator/campaign/s8b_floor_campaign.py:2755` | 同上 | campaign launch、calibration load、receipt 発行の直前。 |
| 8 | `orchestrator/campaign/s8b_oracle_driver.py:762` | `require_current(..., contract_sha256=run_contract["contract_sha256"])` | v2 oracle launch の第一防壁。 |
| 9 | `orchestrator/campaign/s8b_oracle_report.py:1202` | `require_current(..., contract_sha256=contract_sha256)` | v2 manifest の current receipt eligibility。legacy branch は現状維持。 |
| 10 | `orchestrator/campaign/s8b_ratified_freeze.py:960` | `require_current()` | active generation semantics の env admission。 |
| 11 | `orchestrator/campaign/s8b_ratified_freeze.py:1803` | hash 指定付き `require_current()` | journal/receipt を current protocol と照合する。 |
| 12 | `orchestrator/campaign/s8b_ratified_freeze.py:2287` | hash 指定付き `require_current()` | portable run command の current binding。 |
| 13 | `orchestrator/campaign/s8b_ratified_freeze.py:2880` | `require_current()` | current full protocol validation callback。 |
| 14 | `orchestrator/campaign/silo_ladder_rung1.py:1936` | `require_current()` | live environment attestation。 |
| 15 | `orchestrator/campaign/silo_ladder_rung1.py:3534` | `require_current(..., contract_sha256=binding["calibration"]["contract_sha256"])` | 関数名どおり current binding の再検証。 |
| 16 | `orchestrator/campaign/silo_ladder_rung1.py:3752` | `require_current()` | correctness build が使う現行 calibration。 |
| 17 | `orchestrator/campaign/silo_ladder_rung1.py:4433` | `require_current()` | 新規 evidence binding の producer。 |
| 18 | `orchestrator/campaign/pipeline.py:535` | `require_current()` | qualification opt-in の exact current Pegasus 比較。 |
| 19 | `orchestrator/campaign/loop.py:72` | `require_current()` | live measurement contract の current equality gate。 |
| 20 | `orchestrator/campaign/pegasus_floor_scoping.py:75` | `require_current()` | live floor scoping の登録 calibration path。import も `:23` で変更する。 |
| 21 | `orchestrator/campaign/p3_s4_loop_trigger_gating.py:324` | `require_current()` | site admission 後の live P3 contract。alias は `:95` で `_require_current` へ改名する。 |

据え置き・history resolver への置換は0件とする。従って型分離の抜け穴となる legacy `lookup()` caller は残らない。旧 artifact は bytesを書き換えず `GENERATIONS` から g1を解決可能にするが、本 wave の production issuer へ `HistoricalContract` を流さない。

## 5. production 型境界

consumer の呼び出し名だけでなく、次の入口も `CurrentContract` の exact typeへ変更する。

- `orchestrator/campaign/execution_guard.py:55-69,315-329`  
  machine pin、`build_receipt()`、`attest_and_build_receipt()` は `CurrentContract` だけを受ける。
- `orchestrator/campaign/buildcache.py:562-601`  
  `build_v2(..., contract: CurrentContract)` とし、raw/historical wrapperを副作用前に拒否する。
- `orchestrator/campaign/pipeline.py:461-479,745-753`  
  opt-in 値を `Optional[CurrentContract]` にする。既存の `None` legacy 分岐は本 wave では変更しない。
- `orchestrator/campaign/loop.py:62-80`  
  `_authorize_measurement()` の非 `None` 値は exact `CurrentContract` とする。
- `orchestrator/campaign/s8b_oracle_driver.py:699-710,948-957`  
  `_V2Plan.contract` と build provenance guard を `CurrentContract` にする。
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:318-324,338-389,519-524`  
  site admission 後に流す型を一貫して `CurrentContract` にする。

一方、`orchestrator/campaign/env_attestation.py:799-804` の `load_verified_calibration()` は receipt issuer ではないため、次の型を受ける neutral verifier とする。

```python
ExecutionEnvironmentContract | HistoricalContract | CurrentContract
```

wrapper は冒頭で内包 contract に正規化し、`orchestrator/campaign/env_attestation.py:811-873` の path/hash/schema/cross-field 検査は変えない。raw contract の受理は synthetic test用の低水準検証 seamとして残せる。ここから得た `VerifiedCalibration` だけでは発行できず、`execution_guard.py:315-341` が exact `CurrentContract` と calibration SHA を再照合するため、history→receipt の抜け穴にはならない。

## 6. env-literal AST 検査

`V2_ENV_NEUTRAL_MODULES` の免除は `orchestrator/tests/test_env_contract.py:67-86` にある次の1箇所だけを維持する。

```python
("orchestrator/campaign/env_contract.py", "_build_registry")
```

具体的な範囲は、現行 `orchestrator/campaign/env_contract.py:163-194` の単一 `FunctionDef _build_registry` 部分木だけである。

- g1 constructor、世代 tuple、env key、clocks、numactl、calibration path/hashはすべてこの関数内に置く。
- wrapper、transition predicate、generation validator、reverse index、`require_current()` は関数外だが env 中立とする。
- `_build_generations` など別の literal-bearing 関数を新設しない。
- `V2_ENV_NEUTRAL_MODULES` の region 名・対象範囲を増やさない。
- `orchestrator/tests/test_env_contract.py:797-805` の「免除なしなら hit、`_build_registry` だけ免除すれば空」という load-bearing assert は変更しない。

## 7. 既存 `test_env_contract.py` への影響

### 構造変更に伴う機械的追随として変更してよいもの

- `ec.lookup()` の全19箇所  
  `orchestrator/tests/test_env_contract.py:227,243,260,265,273,279,290,332,477,492,547,562,595,608,626,641,715,731,766` を `require_current()` へ移す。
- golden testでは `CurrentContract` の exact typeを確認し、raw dataclassを必要とする `dataclasses.replace()` では `.contract` を明示的に使う。
- `orchestrator/tests/test_env_contract.py:286-292` の代入用サンプルを `CurrentContract` に追随させる。ただし `TypeError` 期待は維持する。
- `orchestrator/tests/test_env_contract.py:301-309` の生 dict 探索は、値が `HistoricalContract`、`CurrentContract`、またはその tuple の場合も検出するよう強化する。旧 `ExecutionEnvironmentContract` だけを探すと恒真化する。
- `orchestrator/tests/test_env_contract.py:312-325,434-436,445-475,518-531` は wrapperを明示的に unwrapするか、read-only propertyを使う。assertする意味・件数は変えない。
- test名の `lookup` は `require_current` / resolver の意味に合わせて改名する。

### 防壁の弱体化になるため書き換えてはいけないもの

- env/calibration golden値: `orchestrator/tests/test_env_contract.py:226-254`
- unknown/non-str が fail-closedになる性質: `:257-265`
- frozen、MappingProxy、register API不在、生 backing dict不在: `:272-325`
- calibration path/hash/schema/semantic admission: `:342-436`
- `len(KNOWN_SELF_INCONSISTENT_CALIBRATIONS) == 1`: `:445-447,490-492`
- `checked_entries == 2`、`required_entries == 1`、既知 self-failure exact set: `:473-475`
- legacy calibration allowlist exact closure: `:518-531`
- `CalibrationRef` の exact field set: `:650-653`
- `ExecutionEnvironmentContract` の exact 6 field set: `:656-664`
- canonical JSON と3つの hash golden、および field変更で hash が変わる性質: `:691-770`
- AST免除 region、非恒真 positive control、bool除外: `:781-838`

特に `ExecutionEnvironmentContract` の field期待へ `generation` 等を足して testを通す修正は禁止する。

## 8. 純増する新規テスト

| 配置候補 | 新しい検出性質 | 落ちる具体的な壊し方 |
|---|---|---|
| `orchestrator/tests/test_env_contract.py:268-325` 周辺 | test側の独立 `EXPECTED_GENERATION_HASHES` と `GENERATIONS` の exact key-set、各列非空、g1保持を照合する。自己申告 keysetから期待を導出しない。 | `GENERATIONS["pegasus"] = (g2,)`、空 tuple、未知 env追加のいずれか。 |
| 同上 | `GENERATIONS` が MappingProxy、各列が tuple、`REGISTRY` の current wrapperが列末尾と同じ raw contract/generationである。 | tupleをlistにする、または独立な `REGISTRY` literalを復活させる。 |
| `orchestrator/tests/test_env_contract.py:109-220` 後 | synthetic successorで calibration path/SHAだけを許し、他の全 field変更を拒否する。no-op successorも拒否する。 | 可変 pointer集合へ `/attestation_mode` を加える。 |
| `orchestrator/tests/test_env_contract.py:222-265` | 全g1 hashの逆引きが exact `HistoricalContract` と generation/envを返し、malformed/未知/wrong-envを拒否する。 | resolverが要求 hashを無視して current先頭要素を返す。 |
| 同上 | `require_current()` は exact `CurrentContract` を返し、指定 hash不一致を拒否し、同じ raw g1でも Historical と nominally別型である。 | `require_current()` が resolver結果をそのまま返す、または指定 hashを無視する。 |
| `orchestrator/tests/test_execution_guard.py:51-87` 周辺 | 同じg1を包む `HistoricalContract` は calibration loadには使えるが、receipt issuerでは副作用前に拒否される。 | `build_receipt()` の型検査を wrapper union または raw contractへ緩める。 |
| `orchestrator/tests/test_env_contract.py:773-838` 周辺 | 独立した production file一覧を AST走査し、`lookup` import/callが0、`resolve_by_contract_sha256` がissuer群で0である。 | 21箇所のうち1箇所を history resolverへ戻す、または legacy `lookup()` を再導入する。 |

既存 test が既に覆う slug、field validation、frozen性、calibration bytes、g1 hash golden、self-inconsistency、env-literal positive controlについては重複する新規 testを追加しない。

## 9. 親 provisional 裁定

### P1 — 賛成

A′-4とA′-5を本 waveへ入れない裁定に賛成する。`orchestrator/campaign/env_contract.py:16-17,197-209` の静的 trust rootを外部 recordへ移すだけでは、全入口のreceipt検査が揃う前にγ-13を弱める。本 waveでは g1だけの独立 generation goldenを置き、追加世代を無断でcurrent化できない状態にする。

### P2 — 賛成

`HistoricalContract` / `CurrentContract` を `ExecutionEnvironmentContract` の subclassにしない裁定に賛成する。composition、別 nominal type、productionでの exact type検査を組み合わせる。wrapper越しの hash は内包 g1へ委譲し、byte preimageには触れない。

### P3 — 賛成

世代列を `env_contract.py` 内へ置く裁定に賛成する。`orchestrator/campaign/env_contract.py:163-194` の `_build_registry` を唯一の env-literal領域として維持し、`GENERATIONS`、reverse index、`REGISTRY` を同じ宣言から導出すれば、権威とAST免除領域を増やさずに済む。

## 検証方針

pytestは実走しない。静的には必読資料の全文、21 production callsite、関連型境界を確認したが、テストが緑であるとは報告しない。

## 総括

- `ExecutionEnvironmentContract` と `_canonical_obj()` は一切変更しない。
- g1 canonical bytesと既存2環境の `contract_sha256` を完全維持する。
- `GENERATIONS` は immutableな世代列、`REGISTRY` はそのcurrent viewとする。
- history/currentは継承なしの別wrapper型で分離する。
- `lookup()` は削除し、21 production callerを `require_current()` へ移す。
- hash逆引きは `HistoricalContract` だけを返し、issuerへ流さない。
- env-literal免除は `_build_registry` の単一 FunctionDefから広げない。
- 既存のpin・凍結bytes・受理集合・self-inconsistency期待は変更しない。