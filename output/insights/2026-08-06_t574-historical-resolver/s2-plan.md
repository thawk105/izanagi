必須入力はすべて読めた。以下は現行行番号を基準にした実装プランであり、実装・編集・pytest 実走は行っていない。

## 現行と変更後の受理集合

production registry は `orchestrator/campaign/env_contract.py:316-326` の bootstrap fuse により全 env が g1 一本である。このため現時点では recorded と current が一致し、表面的な挙動差はない。

| 入口 | 現行で current=g2 / recorded=g1 の場合 | 変更後 |
|---|---|---|
| C1 floor protocol | `s8b_ratified_freeze.py:2878-2881` で current hash と比較して `protocol-invalid` | recorded hash を `expected_env_tag` 付きで一意解決し、g1 を受理 |
| C2 journal | C1 を越えたとしても `:1803` で g2 の calibration / attestation predicate を使う | C1 で得た同一 g1 contract を使用 |
| C3 run command | `:2287` で g2 の `clocks_per_us` / `numactl` を使って再導出 | C1 で得た同一 g1 contract を使用 |
| C4 oracle manifest | `s8b_oracle_report.py:1202-1204` の current lookup + 明示 equality で拒否 | manifest の recorded hash から g1 を解決 |
| 新規 producer | `s8b_floor_campaign.py:308-324` が current g2 のみ受理 | 変更しない。g2 は受理、g1 は拒否 |
| resume admission | `s8b_floor_campaign.py:2750-2755` が current g2 のみ受理 | 変更しない。g1 campaign の resume は拒否 |

変更後も、未知・不正形式・非一意な hash、別 env の hash は拒否する。C4 の legacy manifest、すなわち完全な `run_contract` を持たず現在 `None` になる集合も変えない。

## 解決と注入 seam

resolver callable の契約は C1/C4 で共通にする。

```python
resolver(
    contract_sha256: str,
    *,
    expected_env_tag: str | None = None,
) -> env_contract.GenerationEntry
```

ratified freeze 側は public API に任意 resolver を公開せず、固定 wrapper と注入可能な private core に分ける。

```python
def launch_validate(
    ratified: RatifiedFreeze,
    root=ROOT,
) -> LaunchValidatedFreeze:
    return _launch_validate(
        ratified,
        root=root,
        contract_resolver=_env_contract.resolve_by_contract_sha256,
    )

def _launch_validate(
    ratified: RatifiedFreeze,
    root=ROOT,
    *,
    contract_resolver: Callable[..., _env_contract.GenerationEntry],
) -> LaunchValidatedFreeze:
    ...
```

C1 用 helper は次の形にする。

```python
def _validate_published_protocol(
    document: Mapping,
    *,
    contract_resolver: Callable[..., _env_contract.GenerationEntry],
) -> tuple[dict, _env_contract.ExecutionEnvironmentContract]:
    ...
```

`validate_protocol()` が exact key と non-empty hash/env を確認した後に呼ぶ既存 `contract_sha256_lookup(env_tag)` の closure 内で、

1. `document["contract_sha256"]` を resolver に渡す。
2. `expected_env_tag=env_tag` を必須で渡す。
3. 戻り値が exact `GenerationEntry` であり、contract の env/hash が入力と一致することを再確認する。
4. 正規化 protocol と resolved contract を返す。

resolver は artifact 一件につき一回だけ呼び、C2/C3 では再解決せず同一 contract object を引き回す。これにより途中で current lookup や別 index を再参照する余地をなくす。

C4 は private leaf を次の必須 seam にする。

```python
def _receipt_expectations(
    manifest: Mapping,
    *,
    contract_resolver: Callable[..., env_contract.GenerationEntry],
):
    ...
```

production caller は `env_contract.resolve_by_contract_sha256` を明示して渡す。

## production hunk

以下は変更前の行を anchor とする。

| hunk | 変更前 → 変更後の意味 |
|---|---|
| `orchestrator/campaign/s8b_floor_contract.py:8-10` | callback が「凍結済み hash」を返すという current/historical 不明瞭な説明。→ producer は current、read-only consumer は recorded resolver という caller policy を明記する。 |
| `orchestrator/campaign/s8b_floor_contract.py:138-151` | equality failure が常に `env_contract.lookup(...)` 由来だと表示。→ equality 自体は維持し、診断を `contract_sha256_lookup` policy との不一致に中立化する。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:38` | resolver 型に必要な `Callable` がない。→ private seam の型注釈用に追加する。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:1795-1809` | `_validate_journal` が protocol env から current contract を再 lookup。→ required keyword `contract` を受け、そこから calibration と attestation mode を導出する。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:2088-2090` | journal session の run-command matcher に contract が渡らない。→ `_validate_journal` の resolved contract を渡す。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:2138-2189` | `_validate_result` が run-command matcher に current 解決を委ねる。→ required `contract` を受けて全 result session に渡す。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:2272-2297` | `_run_cmd_matches_portable_session` が `protocol["env_tag"]` を current lookup。→ required `contract` の `clocks_per_us` / `numactl` だけで再導出し、lookup とその例外分岐を除く。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:2300-2304` | occurrence validator に世代情報がない。→ required `contract` を追加する。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:2375-2377` | `/run_cmd` occurrence の許可判定が current-bound。→ occurrence validator が受けた resolved contract を matcher に渡す。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:2745-2752` | public `launch_validate` が直接全処理を持つ。→ `_validate_published_protocol` と resolver-required `_launch_validate` を置き、public wrapper は production resolver を固定して呼ぶ。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:2870-2887` | C1 が `lookup(env).contract_sha256` lambda を使用。→ helper で recorded hash を一回解決し、`protocol, contract` を得る。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:2909-2917` | journal/result に resolved generation が伝播しない。→ 両方へ同じ `contract` を渡す。 |
| `orchestrator/campaign/s8b_ratified_freeze.py:3087-3091` | occurrence/run-command 検査が current contract を再取得。→ 同じ `contract` を渡す。 |
| `orchestrator/campaign/s8b_oracle_report.py:23-25` | resolver seam の `Callable` がない。→ import を追加する。 |
| `orchestrator/campaign/s8b_oracle_report.py:1189-1209` | C4 が current lookup 後に recorded hash と明示比較。→ required resolver で recorded hash + expected env を解決し、その contract で calibration を読む。legacy の `None` 条件は維持する。 |
| `orchestrator/campaign/s8b_oracle_report.py:1365` | `_receipt_expectations(manifest)` の暗黙 current policy。→ production resolver を明示して呼ぶ。 |

`orchestrator/campaign/env_contract.py` は変更しない。特に `validate_generations()` の fuse、`GENERATIONS`、`REGISTRY`、`_CONTRACT_SHA256_INDEX` の production 初期化は不変とする。

`orchestrator/campaign/s8b_floor_campaign.py` も変更しない。残す current lookup は `:313`、`:412`、`:1874`、`:2755` である。`s8b_ratified_freeze.py:960` の env-tag 実在確認も据え置く。

## positive control の具体構成

`test_s8b_ratified_verify.py` の既存 production-emitter fixtureを使い、書込み済み g1 artifact を作った後だけ test view を差し替える。

1. `g1 = EC.GENERATIONS["linux-baremetal"][0].contract` を取得する。
2. `calibration_ref.path` と `sha256` の両方だけを変えた g2 を `dataclasses.replace` で作り、`EC.is_valid_successor(g1, g2)` を確認する。
3. `(GenerationEntry(1, g1), GenerationEntry(2, g2))` を持つ mapping を作る。
4. `_validate_generations_without_bootstrap_fuse(mapping)` は候補列として通す一方、`validate_generations(mapping)` は activation fuse で拒否されることを同じ test で確認する。
5. `_build_contract_sha256_index(mapping)` を test 内だけで既存 index へ `monkeypatch` し、実物の `resolve_by_contract_sha256` が g1 と g2 の両方を解決することを明示的に確認する。g1-only dispatch 表にはしない。
6. `lookup(env_tag)` の test view は g2 を current として返す。production source、`GENERATIONS`、fuse は触らない。
7. public `M.launch_validate(freeze, root)` を呼ぶ。wrapper が resolver seam を private core へ渡し、g1 artifact の C1/C2/C3 が通ることを確認する。resolver spy は一回だけ呼ばれ、run-command matcher 全呼出しの `contract is g1` も確認する。
8. 同じ current=g2 下で `s8b_floor_campaign.validate_protocol(g2_protocol)` は通り、記録済み g1 protocol は `FloorCampaignError` になることを確認する。これは `_run_campaign_core:2750` と CLI `:3483` が通る実 producer admission leaf の positive/negative control であり、実行副作用は起こさない。

これは tmp git fixture 上の component integration であり、live active pointer を使う実環境 E2E ではない。親 brief と probe が示す `[no-active]` を E2E 緑として言い換えない。

C4 も同じ二世代 mapping と current=g2 view を使い、g1 manifest を `_receipt_expectations(..., contract_resolver=...)` へ渡す。返された contract と calibration loader の第1引数が g1 であることを確認する。

## 新規 test nodeid 案

各行の後半が、その test が殺す誤実装である。

| nodeid 案 | 何を殺すか |
|---|---|
| `orchestrator/tests/test_s8b_ratified_verify.py::test_historical_g1_read_only_validation_passes_under_g2_current_but_producer_admission_refuses` | C1/C2 の current 再 lookup、resolver の複数回呼出し、producer の historical 受理、fuse 緩和、g1-only dispatch を殺す。 |
| `orchestrator/tests/test_s8b_ratified_verify.py::test_published_protocol_resolver_fails_closed[unknown-hash]` | 未知 hash を current/fallback へ貼り替える実装を殺す。 |
| `orchestrator/tests/test_s8b_ratified_verify.py::test_published_protocol_resolver_fails_closed[cross-env]` | `expected_env_tag` を渡さない、または戻り値の env binding を検査しない実装を殺す。 |
| `orchestrator/tests/test_s8b_ratified_verify.py::test_published_protocol_resolver_fails_closed[dishonest-resolver]` | 注入 resolver の返却値を無条件に信用し、recorded hash と違う entry を受理する実装を殺す。 |
| `orchestrator/tests/test_s8b_ratified_verify.py::test_run_cmd_projection_uses_resolved_generation_contract[clocks_per_us]` | C3 が渡された contract を無視して current/定数の clock 値を使う実装を殺す。 |
| `orchestrator/tests/test_s8b_ratified_verify.py::test_run_cmd_projection_uses_resolved_generation_contract[numactl]` | C3 が渡された generation の `numactl` を無視する実装を殺す。 |
| `orchestrator/tests/test_s8b_oracle_report.py::test_receipt_expectations_accepts_historical_g1_under_g2_current` | C4 に current lookup、旧 explicit equality、g2 calibration 読出しのいずれかを残す実装を殺す。 |
| `orchestrator/tests/test_s8b_oracle_report.py::test_receipt_expectations_fails_closed[unknown-hash]` | C4 の未知 hash fallback を殺す。 |
| `orchestrator/tests/test_s8b_oracle_report.py::test_receipt_expectations_fails_closed[cross-env]` | C4 で `expected_env_tag` または戻り entry の env/hash 再検査を落とす実装を殺す。 |

C3 の二つの unit では、意図的に clock/numactl の異なる contract を private predicate へ直接渡す。これは登録世代や受理正例には使わず、引数が load-bearing であることだけを確認する。valid successor の統合正例は calibration path/hash だけを変えるため、C3 の current 再 lookup を単独では検出できないからである。

## test hunk と既存 test の更新

| hunk | 変更前 → 変更後の意味 |
|---|---|
| `orchestrator/tests/test_s8b_ratified_verify.py:684-692` | g1/current=g1 の baseline のみ。→ 二世代 positive control と C1 fail-closed matrix を隣接追加する。 |
| `orchestrator/tests/test_s8b_ratified_verify.py:1165-1173` | matcher を contract なしで直接呼ぶ。→ recorded hash から得た contract を渡し、C3 の load-bearing parameterized test を追加する。 |
| `orchestrator/tests/test_s8b_ratified_verify.py:1887-1900` | `_validate_axis_occurrences` を contract なしで呼ぶ。→ fixture env の contract を明示する。 |
| `orchestrator/tests/test_s8b_ratified_verify.py:2065-2100` | `lookup` を required contract に patch して C2 を検査。→ lookup patch を除き、`contract=required` を直接渡して calibration/attestation dispatch を検査する。 |
| `orchestrator/tests/test_s8b_oracle_report.py:1916-1935` | 未知 hash を「registry current との不一致」と期待。→ test 名と期待理由を「未知の contract_sha256」へ更新する。 |
| `orchestrator/tests/test_s8b_oracle_report.py:1938-1972` | current `lookup` を required contract に patch。→ `resolve_by_contract_sha256` が exact `GenerationEntry` を返すよう patch し、expected env と verified calibration を確認する。 |
| `orchestrator/tests/test_s8b_oracle_report.py:1916-1972` の後 | historical g1/current g2 の正例がない。→ C4 の positive/fail-closed matrix を追加する。 |

`orchestrator/tests/test_env_contract.py` は変更不要である。次の既存 test が data 層の依存前提をすでに固定している。

- `:471-480` 二世代候補の純関数受理
- `:540-554` 正当な二世代列も production fuse で拒否
- `:592-600` 全 g1 hash の resolver 正例
- `:602-615` malformed / unknown / wrong-env 拒否
- `:618-632` synthetic index で non-current generation を解決
- `:635-644` 非一意 index の拒否

## caller・fixture・consumer への静的波及

`rg` で確認した直接 caller は以下のとおり。

- `s8b_floor_contract.validate_protocol`:

  - production: `orchestrator/campaign/s8b_floor_campaign.py:320`、`orchestrator/campaign/s8b_ratified_freeze.py:2878`
  - tests: `test_s8b_ratified_freeze.py:284`、`test_s8b_ratified_verify.py:411`、`test_s8b_experiment_numbers.py:113,118,125,131`、`test_s8b_floor_contract.py:116,145,154,161`
  - callback signature は変えないため、診断文以外の caller 修正は不要。

- `s8b_floor_campaign.validate_protocol`:

  - production: `s8b_floor_campaign.py:440,582,2750,3483`
  - tests: `test_s8b_protocol_builder.py:101,167,178,187,417`、`test_s8b_floor_campaign.py:399,997,1002,1007,1016,1036,1053,1061,1075,1082,1427,2472,4688`、`test_s8b_floor_contract.py:175`
  - 全て current policy のまま据え置く。

- `s8b_ratified_freeze.launch_validate`:

  - production: `s8b_oracle_driver.py:511,1066`、`s8b_oracle_report.py:1713`
  - tests: `test_s8b_ratified_freeze.py:1198,1280`、`test_s8b_oracle_driver.py:3810,4110,4140`
  - `test_s8b_ratified_verify.py:201,692,884,887,897,905,916,933,938,951,959,967,977,987,999,1025,1037,1050,1062,1077,1092,1112,1122,1133,1141,1162,1173,1219,1230,1249,1259,1270,1281,1292,1303,1315,1350,1468,1577,1590,1834,1853,1863,1926,1937,1947,1960,1976,1987,1995,2009,2020,2045,2060`
  - public signature は維持するため既存 caller は変更不要。

- private predicate caller:

  - `_validate_journal`: production `s8b_ratified_freeze.py:2909`、direct test `test_s8b_ratified_verify.py:2092`
  - `_validate_result`: production `s8b_ratified_freeze.py:2914` のみ
  - `_run_cmd_matches_portable_session`: production `s8b_ratified_freeze.py:2088,2184,2375`、direct test `test_s8b_ratified_verify.py:1170`
  - `_validate_axis_occurrences`: production `s8b_ratified_freeze.py:3087`、direct test `test_s8b_ratified_verify.py:1894`
  - `_receipt_expectations`: production `s8b_oracle_report.py:1365` のみ。`test_s8b_oracle_report.py:1916-1972` は `build_observations` 経由の間接 consumer。

共有 fixture の波及は次の範囲に限定される。

- `test_s8b_ratified_verify.py:34` が `test_s8b_ratified_freeze` を共有し、`:571-590` の `_build_launch_repo` が production emitter を利用する。
- 共有元は `test_s8b_ratified_freeze.py:282-303` `_emitter_protocol`、`:381-389` `_emitter_measure`、`:427-478` `_prepare_emitter_base`、`:758-962` `build_production_emitter_g1`、`:965-967` `load_emitter_g1`。
- oracle 側は `test_s8b_oracle_report.py:24` で同 fixture module を importし、`:191-226` `_manifest` と `:360-386` `_campaign_start` を再利用する。
- `orchestrator/tests/conftest.py:108-141` の autouse isolation はそのまま使用し、新しい共有 fixture や real-repo serial 登録は追加しない。

current のまま残す別入口は `orchestrator/campaign/loop.py:62-75`、`pipeline.py:535`、`p3_s4_loop_trigger_gating.py:95` である。

## 親の P1〜P5 への意見

| 項目 | 意見 | 根拠 |
|---|---|---|
| P1 | 修正採用 | 既存 resolver と新規 module mutable state 不要には賛成。ただし各 predicate が個別解決するのでなく、artifact ごとに一回解決して exact contract を C2/C3 へ渡す。public API は resolver を任意注入可能にしない。 |
| P2 | 採用 | generation 番号別 dispatch 表は不要。resolved contract の calibration、attestation、clock、numactl が predicate dispatch そのものである。C3 は valid successor では値が変わらないため、別途 private-unit で load-bearing 性を固定する。 |
| P3 | 採用 | equality の単純削除ではなく、hash→entry の一意解決、expected env、返却 entry の env/hash 再検査へ置換する。未知 hash の拒否は維持する。 |
| P4 | 修正採用 | resume を current に残す結論は scope どおり。ただし「Pegasus は allow_resume=False なので現実の受理集合は変わらない」という一般化には反対する。`env_contract.py:245` の linux-baremetal は `allow_resume=True` であり、将来の current 更新時には実際の availability loss になる。 |
| P5 | 修正採用 | 正例の形は採用するが、g1 artifact を通すだけでは不十分。resolver が g1/g2 の両方を解決すること、g2 producer positive、g1 producer negative、public fuse の拒否を同じ control で示す。 |

D197 の activation identifier は本 scope では生成・直列化しないため、新しい activation field や仮の receipt は追加しない。

## 実装順序と依存

1. `s8b_floor_contract` の callback policy 文言と診断を中立化する。API は変えない。
2. ratified freeze に固定 public wrapper、resolver-required core、C1 helper を追加する。
3. C1 が返す contract を C2/C3 の全 internal edge へ原子的に通す。途中状態では required 引数が欠けるため、C1〜C3 は同一単位で実装する。
4. 独立単位として C4 を resolver-required にし、production caller を更新する。
5. direct private caller を更新後、二世代 positive control、fail-closed matrix、C3 load-bearing unit を追加する。
6. producer/current 入口と残存 lookup を `rg` で再分類し、変更後の current lookup が producer/admission と `s8b_ratified_freeze.py:960` だけであることを確認する。
7. `output/` や既存 publish bytes は編集しない。実装後に `orchestrator/qualification/contract.py:62`、`silo_ladder_rung1.py:260`、`s8b_oracle_manifest.py:46` と output pin を再検索する。`env_contract.py` は変更しないためその source hash は動かさない。
8. 書込可能な実装環境では py_compile、対象 nodeid、`python3 tools/run_tests.py`、mutation matrix、`check_codex_agents.py`、`check_docs.py`、commit 後の provenance 監査の順で検証する。

このプラン作成では pytest を一切実行しておらず、静的な `rg` / 読取りだけである。テストが緑だという主張はしていない。

## 総括

- recorded hash を一度だけ解決し、同一 contract を C1〜C3へ、C4 は manifest 単位で解決する。
- 最大リスクは resolver seam の env/hash binding 漏れと、C3 の引数が実質未使用になることである。
- producer・resume・bootstrap fuse は current のまま維持し、read-only consumer だけを拡張する。
- 親 brief への主な反対点は P4 の影響評価であり、linux-baremetal の resume 受理集合には実害があり得る。