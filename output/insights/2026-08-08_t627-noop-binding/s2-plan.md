## 判定

**条件付き GO** とする。推奨は、loader に `ActiveContract -> ActiveContract` の successor 判定 callable を必須注入し、production 側 adapter が両行を exact `GenerationEntry` に解決した後で `is_valid_successor` を呼ぶ構成である。

条件は次の 3 点。

- 親 brief の「実装は activation 本体＋同テストだけ」という所有範囲を、`env_contract.py` と issuer の結線変更まで広げる。
- callable は必須 keyword とし、既定値や「未指定なら generation だけで判定」は置かない。
- 既存 3 テストに加え、変更後に別理由で偶然通る `test_issued_valid_suffix_is_not_active_until_source_head_update_and_restart` も修復する。

この範囲拡張を認めず、親 brief (P2) の plain registry 投影だけで済ませるなら **NO-GO**。loader の入力上に `is_valid_successor` との合成が現れず、裁定 (b) を直接検査できないためである。

## 推奨する束縛

実 schema の 1 行を分解せず、`ActiveContract(env_tag, generation, contract_sha256)` のまま predecessor / successor として渡す。

```text
record の ActiveContract
  → loader が (env_tag, generation, hash) を registered catalog と exact 照合
  → production adapter が同じ ActiveContract を GenerationEntry に exact 解決
  → その 2 個の GenerationEntry.contract を is_valid_successor へ渡す
```

serial 2 以降の各 env は次の規則にする。

1. `(generation, contract_sha256)` が前行と完全一致なら据置。
2. 変化した場合は `new.generation == old.generation + 1`。
3. さらに production adapter が両行を、それぞれ同じ generation と hash の `GenerationEntry` に解決できる。
4. 解決した contract 間で `is_valid_successor(old.contract, new.contract) is True`。
5. 全 env 据置なら no-op として拒否。

env 集合は既存の exact 一致検査で先に拒否されるため変更しない。serial 1 は遷移を持たず、既存の registry 照合だけを受ける。

### 設計案の比較

| 案 | `is_valid_successor` との合成 | import / pure leaf | 評価 |
|---|---|---|---|
| 親 (P2): plain `(generation, hash)` catalog の隣接だけを見る | production の module 初期化履歴にだけ間接依存。loader の型・入力には証拠がない | 最小、pure leaf 維持 | 不採用。任意 catalog を受ける loader 単体では裁定 (b) を固定できない |
| `GenerationEntry` mapping を loader に渡す | 最も直接的 | activation → env_contract の逆 import が生じる。env_contract は現在 activation を遅延 import しており、循環と [`pure leaf` テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:842) の破壊を招く | 不採用 |
| successor callable を必須注入 | exact record 行を adapter が GenerationEntry に解決し、直接 `is_valid_successor` を呼べる | activation は stdlib-only のまま。runtime import は従来どおり env_contract → activation の一方向 | **推奨** |
| 許可 edge の data catalog を別途渡す | builder 時点では合成できるが、loader には再び投影結果しか残らない | pure leaf は維持 | plain catalog と同じ信頼問題に加え、二重 catalog の不整合面が増える |

callable 自体は信頼 capability であり、任意 caller が偽 callable を渡せる点は認証機構では解消しない。ただし expected head や registered catalog と同様、production caller を閉じてその配線をテストすることで authority 境界を明示できる。adapter は immutable な `GENERATIONS` を読むだけで I/O を行わない。

循環 import は次の形で避ける。

- `env_contract_activation.py` は `env_contract` を一切 import しない。
- `env_contract.py` は型注釈だけ `TYPE_CHECKING` 下で `ActiveContract` を参照する。
- exact 型検査が必要な adapter 本体では activation を局所 import する。実行時点では `_load_authority_snapshot` が既に activation を import 済みであり、逆方向 import はない。
- [`test_activation_leaf_is_stdlib_only_campaign_import_free_and_env_neutral`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:842) は緩和・削除せず、そのまま保持する。

## file:line 実装計画

行番号は現行 bytes 基準。

### `orchestrator/campaign/env_contract_activation.py`

- [`:10`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:10)
  - `collections.abc` の import に `Callable` を追加する。
- [`:67`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:67)
  - `ActiveContract` 定義直後に次の型 alias を置く。

```python
_RegisteredSuccessorPredicate = Callable[
    [ActiveContract, ActiveContract],
    bool,
]
```

- [`:250`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:250)
  - `validate_activation_records` の直前に private gate を挿入する。

```python
def _validate_activation_transition(
    predecessor_rows: tuple[ActiveContract, ...],
    successor_rows: tuple[ActiveContract, ...],
    *,
    activation_serial: int,
    is_valid_registered_successor: _RegisteredSuccessorPredicate,
) -> None:
```

  - `env_tag -> predecessor row` を作り、同じ env の exact `(generation, contract_sha256)` を比較する。
  - 変化行は exactly `+1` を要求してから callable を呼ぶ。
  - callable の返り値は `type(value) is bool` を要求する。
  - callable が通常例外を投げた場合は `ActivationRecordError` に包み直す。
  - 1 行以上の正当な前進がなければ no-op を拒否する。

例外メッセージの骨子は以下に固定する。

- `activation transition の env 対応が不一致: serial=...`
- `activation generation 遷移が exactly +1 でない: serial=... env_tag=... gX -> gY`
- `registered successor 判定中に例外: serial=... env_tag=...`
- `registered successor 判定値が exact bool でない: ...`
- `generation/hash 束縛済み contract が正当な successor でない: ...`
- `activation transition が全 env 据置の no-op: serial=...`

- [`:251–257`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:251)
  - public signature に既定値なしの keyword-only 引数を追加する。

```python
def validate_activation_records(
    records: Sequence[tuple[str, bytes]],
    *,
    registered_contracts: Mapping[str, tuple[tuple[int, str], ...]],
    is_valid_registered_successor: _RegisteredSuccessorPredicate,
    expected_head_serial: int,
    expected_head_state_sha256: str,
) -> ActivationState:
```

- [`:264`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:264)
  - record が 1 件しかない場合も結線漏れを検出できるよう、chain loop より前で `callable(...)` を検査する。
  - エラー骨子は `is_valid_registered_successor は callable でなければならない`。
- [`:274`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:274)
  - `previous_rows: tuple[ActiveContract, ...] | None = None` を追加する。
- [`:291–308`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:291)
  - 現 record の env 集合と全 `(generation, hash)` が catalog に照合された後、`previous_rows` があれば `_validate_activation_transition` を呼ぶ。
  - その後にだけ `previous_rows = rows` と chain state を更新する。
- [`:384–397`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:384)
  - `load_activation_state` にも同じ必須 keyword と型を追加し、`validate_activation_records` へそのまま転送する。

schema key、canonical bytes、`ActiveContract`、`ActivationState` の形は変更しない。

### `orchestrator/campaign/env_contract.py`

- [`:33`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:33)
  - `TYPE_CHECKING` を追加し、型検査時だけ `ActiveContract` を import する。
- [`:389–392`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:389)
  - `_REGISTERED_CONTRACT_CATALOG` の直後へ次の 2 helper を挿入する。

```python
def _resolve_activation_entry(
    row: ActiveContract,
) -> GenerationEntry | None:
    ...

def _is_valid_activation_successor(
    predecessor: ActiveContract,
    successor: ActiveContract,
) -> bool:
    ...
```

`_resolve_activation_entry` は以下をすべて満たす場合だけ entry を返す。

- exact `activation.ActiveContract`
- `GENERATIONS[row.env_tag][row.generation - 1]` が存在
- `type(entry) is GenerationEntry`
- `entry.generation == row.generation`
- `entry.contract.env_tag == row.env_tag`
- `entry.contract.contract_sha256 == row.contract_sha256`

adapter は env が同じことと両解決の成功を確認し、最後にだけ次を返す。

```python
is_valid_successor(predecessor_entry.contract, successor_entry.contract)
```

generation delta は loader の責務とし、adapter へ重複実装しない。これにより `+2` を callable が誤って受理しても loader 側の数値 gate が独立して発火する。

- [`:476–486`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:476)
  - `_load_authority_snapshot` の `activation.load_activation_state(...)` に以下を追加する。

```python
is_valid_registered_successor=_is_valid_activation_successor,
```

以下は変更しない。

- [`_validate_generations_without_bootstrap_fuse`:304–339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:304)
- [`_build_registered_contract_catalog`:379–389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:379)
- [`_ACTIVATION_HEAD_*`:370–373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:370)

### `tools/issue_env_contract_activation.py`

- [`:206–211`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/tools/issue_env_contract_activation.py:206)
  - 既存 loader 呼出しへ次を追加する。

```python
is_valid_registered_successor=contract._is_valid_activation_successor,
```

issuer 固有の delta / successor 実装は追加しない。組み立てた suffix を既存 chain と一緒に loader へ渡す単一 gate を維持する。

### `orchestrator/tests/test_env_contract_activation.py`

- [`:47–55`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:47)
  - synthetic catalog 用に、許可する exact `ActiveContract` edge を列挙した `_is_synthetic_successor` を追加する。
- [`:84–102`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:84)
  - 任意の state 列から canonical chain を作る helper を追加。
  - `_validate` に predicate override を持たせ、既定は `_is_synthetic_successor` とする。
- 現行 direct call の [`:338`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:338)、`:348`、`:366`、`:404`、`:419`、`:443`、`:457`、`:500`
  - 必須 callable を明示する。移動・分割される `:500` の mismatch ケースも削除せず独立 node にする。
- [`:296–301`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:296)
  - production record の direct `load_activation_state` には `ec._is_valid_activation_successor` を渡す。
- [`:572–588`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:572)
  - production loader spy に、head 定数だけでなく
    `observed["is_valid_registered_successor"] is ec._is_valid_activation_successor`
    も追加する。

## 受理集合の前後

前提は canonical bytes、正しい hash chain/head、同一 env 集合、各 record 行が catalog と一致していること。

| ケース | 変更前 | 変更後 | 理由 |
|---|---:|---:|---|
| serial 1 単独 | 受理 | 受理 | 遷移規則は発火しない |
| `(0, +1)`、+1 は正当 successor | 受理 | 受理 | 一部据置を許す |
| `(+1, +1)`、双方正当 successor | 受理 | 受理 | 複数 env 同時前進を許す |
| `g1 → g2 → g3` の全リンクが正当 | 受理 | 受理 | terminal だけでなく各隣接 pair を検査 |
| `(0, 0)` no-op | 受理 | **拒否** | D228 の存在条件 |
| `(+2, 0)` skip | 受理 | **拒否** | changed env は exactly +1 |
| `(-1, 0)` downgrade | 受理 | **拒否** | 負 delta |
| **`(+2, −1)` 相殺** | 受理 | **拒否** | 総和ではなく env ごとに検査 |
| `(+1, 0)` だが bound contract が `is_valid_successor=False` | 受理可能 | **拒否** | T-627 (b) の追加縮小 |
| env 追加・削除 | 拒否 | 拒否 | 既存 exact env 集合 gate |
| 未登録 generation | 拒否 | 拒否 | 既存 catalog gate |
| generation と hash の食い違い | 拒否 | 拒否 | 既存 pair gate |
| filename/serial/predecessor/head 不整合 | 拒否 | 拒否 | 既存 chain/head gate |

最後から 5 行目は、現在の production `GENERATIONS` では import-time の `validate_generations` が先に拒否するため通常構成できない。それでも loader と adapter の合成を独立に固定し、「番号だけ」の退行を検出するため synthetic node を置く。

過剰拒否は起こさない。具体的な正例は以下。

- pegasus だけ `g1 → g2`、linux-baremetal は g1 据置。
- 複数 env が同時に各 `+1`。
- 将来 g3 が登録された場合の `g1 → g2 → g3`。
- 単独 bootstrap record。
- forward activation 後、古い g1 を ever-active history として解決すること。

「全 env が +1」「1 env だけが +1」といった未裁定の制限は導入しない。

## 既存テストの再著述

### 1. 旧 delta 非強制テスト

[`test_chain_intentionally_does_not_enforce_generation_delta_predicates`:465–505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:465) は削除ではなく、後述の独立 node 群へ完全置換する。

- no-op / skip / downgrade の「受理期待」は裁定による受理集合縮小なので反転する。
- 末尾の wrong-hash rejection は既存保証であり、独立 node に移して保持する。
- `expected` 緩和、skip、削除は行わない。

### 2. downgrade を使った historical fixture

[`_actual_serial3_downgrade`:133–148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:133) は削除する。

[`test_downgrade_preserves_pegasus_g2_for_historical_resolution`:662–676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:662) は次へ改名・再構成する。

```python
def test_forward_activation_preserves_pegasus_g1_for_historical_resolution(...):
    second = _actual_serial2(authority)  # g1 → g2
    with _use_authority(..., second):
        assert ec.lookup("pegasus") is ec.GENERATIONS["pegasus"][1].contract
        g1 = ec.GENERATIONS["pegasus"][0]
        assert g1.contract.contract_sha256 in (
            ec.current_activation_state().ever_active_contract_sha256s
        )
        assert ec.resolve_by_contract_sha256(
            g1.contract.contract_sha256,
            expected_env_tag="pegasus",
        ) is g1
```

変更されるのは「downgrade chain を受理する」という旧期待である。ever-active な歴史世代を解決できるという consumer 保証は変更せず、正当な forward chain で維持する。

既存 [`test_serial2_preserves_g1_as_ever_active_and_verifies_history_on_resolution`:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:646) は lazy calibration verification を検査しているため残す。再著述 node は state の ever-active 集合と resolver の意味を検査し、役割を区別する。

### 3. issuer success

[`test_issue_main_success_prints_required_head_and_inactive_warning`:980–1025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:980) は引数を次へ変える。

```text
linux-baremetal=1
pegasus=2
```

さらに発行 document の pegasus 行が generation 2 / g2 hash であり、linux-baremetal が g1 据置であることを assert する。handoff 出力の厳密な期待は維持する。

別 node `test_issue_main_rejects_noop_without_publishing` で従来の `g1/g1` 入力を与え、exit code 1、`no-op` 診断、`00000002.json` 不在を assert する。

### 4. 親 brief が拾っていない masked test

[`test_issued_valid_suffix_is_not_active_until_source_head_update_and_restart`:539–569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:539) も現在 `active_contracts=current.active_contracts` で no-op suffix を作っている。

変更後は EnvContractError 自体は出るため偶然緑になり得るが、head pin ではなく transition gate で落ちる。これは期待変更ではなく fixture の破損である。

- suffix を pegasus g2 への正当な forward record にする。
- 例外 match を一般的な `activation authority 検証失敗` から、内側の `activation head (serial|state hash) 不一致` まで確認する形に強める。
- issuer の create-only 経路を使うという元のテスト目的は維持する。

## 新規テスト node 設計

すべて独立 node とし、no-op / skip / downgrade を parametrize で一括しない。

| node 名 | fixture と assert | 検出する退行 |
|---|---|---|
| `test_transition_accepts_one_plus_one_with_other_env_unchanged` | `(1,1)→(2,1)`、terminal と ever-active を exact assert | 一部据置の過剰拒否 |
| `test_transition_accepts_multiple_simultaneous_plus_one` | `(1,1)→(2,2)` を受理 | 「1 env だけ」への過剰縮小 |
| `test_transition_rejects_all_env_noop` | `(1,1)→(1,1)`、`no-op.*serial=2` | 存在条件の欠落 |
| `test_transition_rejects_noop_in_middle_of_chain` | `(1,1)→(2,1)→(2,1)`、serial 3 で拒否 | terminal pair しか見ない実装 |
| `test_transition_rejects_skip_even_when_successor_predicate_accepts` | `(1,1)→(3,1)`、callable は常に `True`、`g1 -> g3` で拒否 | **hash だけを見る誤実装** |
| `test_transition_rejects_downgrade_even_when_successor_predicate_accepts` | `(2,1)→(1,1)`、callable は `True` | 負 delta の欠落 |
| `test_transition_rejects_compensating_plus_two_minus_one` | **`(1,2)→(3,1)`**、callable は `True` | 総和 `+1` で相殺する誤実装 |
| `test_transition_rejects_plus_one_when_bound_contract_successor_is_false` | `(1,1)→(2,1)`、callable は `False`、successor 診断 | **番号だけを見る誤実装** |
| `test_successor_predicate_receives_exact_generation_hash_rows` | spy が old/new の exact `ActiveContract` と 1 回だけ呼ばれたことを assert | generation/hash の分離、据置 env への誤呼出し |
| `test_record_rejects_registered_generation_with_wrong_contract_hash` | serial 2 を `g2 + predecessor hash` にして registry mismatch | 既存 pair gate の消失 |
| `test_transition_rejects_non_bool_successor_result` | callable が `1` を返す、exact-bool 診断 | truthy fail-open |
| `test_transition_wraps_successor_exception_fail_closed` | callable が `RuntimeError`、`ActivationRecordError` と cause を assert | callback 障害の fail-open |
| `test_production_successor_adapter_resolves_bound_generation_entries` | real pegasus g1/g2、`ec.is_valid_successor` spy が exact contract object 2 個を受ける | catalog だけで済ませる退行 |
| `test_issue_main_rejects_noop_without_publishing` | issuer の g1/g1、exit 1、suffix 不在 | issuer が loader gate を迂回する退行 |

`(+2, −1)` node では callable を `True` に固定する。これにより拒否理由を generation gate 一つに限定し、successor adapter に偶然救われるテストにしない。

## 波及

- [`execution_guard.py:44–104`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/execution_guard.py:44)
  - 変更不要。検証済み `ActivationState` の current row を再度 `GENERATIONS` と照合する consumer であり、loader の受理集合縮小だけを受ける。
  - activation が env_contract を逆 import する案では、同ファイルの両 module import が循環面になるため、その案を採らない。
- [`orchestrator/tests/conftest.py:43–96`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/conftest.py:43)
  - 変更不要。fixture は synthetic `GENERATIONS` と catalog を同時に差し替えるが、作る chain は serial 1 一件なので successor callable は呼ばれない。
  - `_load_authority_snapshot` が必須 callable を渡すため結線自体は成立する。将来 fixture が serial 2 を作る場合も adapter は monkeypatch 後の `GENERATIONS` を読む。
- [`silo_ladder_rung1.py:254–285`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/silo_ladder_rung1.py:254)
  - `env_contract.py` と activation leaf は runtime-module binding に含まれるため、将来生成する binding の source hash は変わる。
  - 既存凍結成果物は歴史 binding なので bytes を更新しない。
- [`silo_ladder_rung1.py:1938`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/silo_ladder_rung1.py:1938)、[`:3530`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/silo_ladder_rung1.py:3530)、[`:3755`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/silo_ladder_rung1.py:3755)、[`:4438`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/silo_ladder_rung1.py:4438)
  - いずれも `lookup("pegasus")` の consumer。production record が serial 1 のままなので返り値は不変、コード変更不要。
- `test_silo_ladder_rung1_driver.py:926`、`test_t419_probe_causality.py:1586`、`test_t126_pegasus_tools.py:1428`
  - path membership または動的 hash を検査しており、literal な現行 source hash の更新対象ではない。
- `s8b_floor_campaign.py`、`s8b_ratified_freeze.py`、`s8b_oracle_report.py`
  - `resolve_by_contract_sha256` の downstream。forward chain でも ever-active 集合は全 record の hash を保持するため変更不要。
- source-stage helper [`test_env_contract_activation.py:151–185`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:151)
  - env_contract と activation を既に overlay するためファイル一覧変更不要。
- repo 内の direct caller は `_load_authority_snapshot`、issuer、同テストファイルだけである。必須 signature の更新漏れはこの閉包で尽くせる。

## 不変条件と検証状態

- [`00000001.json`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activations/00000001.json:1) は変更しない。
- `_ACTIVATION_HEAD_SERIAL = 1` と `_ACTIVATION_HEAD_STATE_SHA256 = f7807285…` は変更しない。
- production chain は 1 record なので遷移 helper は呼ばれない。静的には `ActivationState` の serial、state hash、active rows、ever-active 集合、および両 `lookup()` の g1 contract は不変である。
- docs、凍結成果物、head pin、commit は対象外。
- sandbox は read-only のまま使用し、ファイル変更は一切行っていない。
- pytest、import 実走、build は行っていない。したがって緑は主張しない。本回答は `sed` / `rg` による静的読解だけに基づく。

## 総括

親 (P2) の registry 投影だけでは、loader の契約上 `GenerationEntry` と `is_valid_successor` の合成が暗黙のまま残る。必須 callable と production adapter を用いれば、実 record の同じ `(env_tag, generation, contract_sha256)` 行を exact `GenerationEntry` に解決してから successor 判定でき、activation leaf の stdlib-only 性と import 方向も維持できる。

よって、`env_contract.py` と issuer を実装範囲へ加え、既存 3 件と masked な valid-suffix テストを再著述することを条件に **GO** とする。