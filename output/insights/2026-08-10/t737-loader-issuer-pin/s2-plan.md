# 実装プラン

静的読解のみ。ファイル編集・pytest 実走はしておらず、以下の検証結果はすべて未実走である。production コード、新規依存、既存 77 node の期待値・helper 署名は変更しない。

## 1. 合成 registry と共通 helper

編集対象は [orchestrator/tests/test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:59) のみ。

### registry

`FOUR_ENV_CATALOG` 後の現行 `:59-70` に `_PIN_ENV_COUNT = 65` と `_synthetic_registry()` を追加する。

- env_tag は `pin-env-000`〜`pin-env-064`。ゼロ埋めにより `sorted()` の最後が必ず `pin-env-064` となり、実 env 名とも衝突しない。
- `ec.GENERATIONS["linux-baremetal"][0].contract` を基礎に `dataclasses.replace` で env_tag と calibration_ref だけを変更する。
- 全 env に g1/g2、最後の env だけ g3 を持たせる。したがって catalog は 65 env・131 generation row。
- calibration path は `output/synthetic-activation/<env_tag>/g<generation>.json`、SHA は既存 `hashlib.sha256(f"{env_tag}:g{generation}".encode("ascii"))` から作る。
- 同じ env 内では calibration path/SHA の対だけが変わるため、[env_contract.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/env_contract.py:211) の実 `is_valid_successor` で g1→g2、g2→g3 が True になる。
- `ec.validate_generations(generations)` (`env_contract.py:345-350`) を factory 内で通し、連番・hash 一意性・隣接 successor を fixture 自身の前提検査にする。
- catalog は production の `_build_registered_contract_catalog` (`env_contract.py:382-392`) と同じ変換で、各 `GenerationEntry` の `(generation, contract_sha256)` を `MappingProxyType` にする。
- calibration ファイル自体は作らない。採る loader 入口は activation leaf であり、issuer は current state を明示注入するため、これらを読む経路はない。

### record

現行 `_chain` (`test_env_contract_activation.py:130-154`) を署名変更なしで再利用する。

- serial 1: `(1,) * 65`
- G 違反の serial 2: `(2,) * 64 + (3,)`
- P 違反および正例の serial 2: `(2,) * 65`

`_chain` は `activation.build_activation_record` を呼び、前 record の `activation_state_sha256` を次 record の predecessor に設定する。さらに既存 `_raw` (`:92-94`) が `canonical_record_bytes(document) + b"\n"` を作るため、serial 1/2 とも canonical bytes になる。

現行 `_chain` 後の `:154` に次の新規 helper を置く。

- `_write_raw_records(directory, records)`: directory を作り、`_chain` が返した `(filename, raw)` を変換せず書く。
- `_initial_state_from_head(head)`: serial 1 document の rows から exact `ActivationState` を作り、issuer の `current_activation_state` seam に渡す。
- `_active_argv(env_tags, target_generations)`: 各 env について `("--active", f"{env_tag}={generation}")` を平坦化し、`argv.count("--active") == 65` と長さ整合を assert する。

既存 helper の扱いは次のとおり。

| helper | 扱い |
|---|---|
| `_chain` | serial 1/2 の chain と head hash 作成に再利用 |
| `_raw` | `_chain` 内から再利用。直接呼出しは不要 |
| `_write` | 不使用。document 用 helper なので、既に canonical な raw bytes を decode/re-encodeしない |
| `_validate` | 不使用。private validation 直叩きとなり、今回の integration scope を満たさない |
| `_load_issue_tool` | 層 2 の全 node で再利用 |
| `_use_authority` | 不使用。`ec.current_activation_state()` と calibration 検証を伴う実 registry 向け helper で、合成 contract には適さない |

既存 helper の署名・戻り値・既存呼出しは一切変えない。

## 2. 層 1 は `activation.load_activation_state` を採る

呼出し先は [env_contract_activation.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/env_contract_activation.py:479)。

各 node は `ec.GENERATIONS` だけを合成 mapping に差し替え、次を直接渡す。

```python
activation.load_activation_state(
    authority,
    registered_contracts=catalog,
    is_valid_registered_successor=ec._is_valid_activation_successor,
    expected_head_serial=head["activation_serial"],
    expected_head_state_sha256=head["activation_state_sha256"],
)
```

これにより filesystem reader `:450-476`、record validator `:332-422`、量化点 G/P `:275/:300` を実際に通す。独自 predicate ではなく production adapter を使う。

追加位置は既存 production-loader 群の後、現行 `test_env_contract_activation.py:1564` 付近。

1. `test_production_loader_rejects_65th_env_generation_skip`

   - serial 2 は先頭 64 env が g1→g2、最後だけ g1→g3。
   - `ActivationRecordError` の `exactly +1`、`pin-env-064`、`g1 -> g3` を同時に match する。

2. `test_production_loader_rejects_65th_changed_env_invalid_successor`

   - serial 2 は全 65 env が g1→g2。
   - fixture 構築・`ec.validate_generations` 後に限り、`ec.is_valid_successor` を「元の predicate が True かつ successor.env_tag が最後でない」に patch する。
   - adapter 自体は実物のまま通し、最後だけ False にする。
   - `ActivationRecordError` の `successor でない` と `pin-env-064` を match する。

### `ec.current_activation_state()` まで上げない理由

`current_activation_state()` (`env_contract.py:631-633`) は `_authority_snapshot` (`:576-586`) から `_load_authority_snapshot` (`:519-548`) へ進む。activation が正例を返すと、`:535-542` が全 active row に対して `_verify_entry_calibration` を必ず呼ぶ。

同 verifier は `:486-516` で実 calibration bytes と admission semantics を読む。このため、必須の正例まで同じ入口で通すには次のどちらかが必要になる。

- `_verify_entry_calibration` を no-op patch して correctness gate を迂回する。
- 65 本の schema-valid calibration 成果物を別途合成する。

前者は「production loader を通した」という主張を弱め、後者は遷移量化 pin を calibration schema に不必要に結合する。したがって P2 の leaf 入口を採る。

上位から leaf への結線自体は `env_contract.py:524-530` が catalog・adapter・head を直接渡している。既存 `test_production_loader_passes_source_head_constants_to_leaf` (`test_env_contract_activation.py:1544-1564`) は head と adapter identity を固定している。ただし catalog identity は現行 test が assert していないため、ここは後述の親裁定点とする。

## 3. 層 2 の issuer 経路

issuer helper は既存 `_load_issue_tool` (`test_env_contract_activation.py:1835-1841`) の直後に置く。

各 issuer node は、serial 1 だけを書いた専用 authority directory と `_initial_state_from_head` の state を用意する。argv は env_tag 順に65組、計130要素とする。

```python
[
    "--active", "pin-env-000=2",
    ...
    "--active", "pin-env-064=2",  # P/正例
]
```

G だけ最後を `pin-env-064=3` にする。

これは issuer の exact env 集合検査 `issue_env_contract_activation.py:167-177`、row 構築 `:180-201`、既存 record 読込 `:205`、production validation `:206-212` を通る。

### monkeypatch の最小集合

| 属性 | 対象 node | 理由 |
|---|---|---|
| `ec.GENERATIONS` | 全 issuer pin | 65 env の assignment 解決と adapter の generation 解決 |
| `ec._REGISTERED_CONTRACT_CATALOG` | 全 issuer pin | `issuer.main` が `:208` で validator に渡す catalog |
| `ec.current_activation_state` | 全 issuer pin | 合成 serial 1 state を返し、無関係な calibration load を避ける |
| `ec._ACTIVATION_DIRECTORY` | 全 issuer pin | `tmp_path/authority` の絶対 `PurePosixPath` |
| `issuer.__file__` | 全 issuer pin | mutant が成功経路へ抜けた場合も、handoff の `relative_to(repo_root)` を tmp 内で完走させる |
| `ec.is_valid_successor` | P pin のみ | 最後の env だけ False にしつつ production adapter を維持 |

`_ACTIVATION_DIRECTORY` を絶対 path にするため、`ec._repository_root` は patch しない。`Path(root) / absolute_path` は absolute 側を採用し、`_repository_root` の directory sentinel (`env_contract.py:472-479`) も同じ tmp authority を確認できる。

`activation.validate_activation_records` と `issuer._write_create_only` も patch しない。したがって拒否は publish 前の `issue_env_contract_activation.py:206-212` で起き、正例は実 writer `:213` を通る。

3. `test_issue_main_rejects_65th_env_generation_skip_without_publishing`

   - 65 個の `--active`、最後のみ g3。
   - `SystemExit.code == 1`。
   - stderr に `exactly +1`、最後の env、`g1 -> g3`。
   - 実行前後とも `authority / "00000002.json"` が存在しないことを assert。

4. `test_issue_main_rejects_65th_changed_env_invalid_successor_without_publishing`

   - 全 env g2、`ec.is_valid_successor` は最後のみ False。
   - `SystemExit.code == 1`。
   - stderr に `successor でない` と最後の env。
   - `00000002.json` 不在を assert。

### `_is_valid_activation_successor` を patch しない理由

adapter は `env_contract.py:395-414` で `ActiveContract` を現在の `GENERATIONS` に generation/hash exact で解決し、`:417-432` で実 contract を `is_valid_successor` に渡す。

これを直接 patch すると、issuer が `:209` で production adapter を渡していても、generation/hash 解決を通った証拠が消える。合成 `GENERATIONS` と catalog の食い違いも隠せるため、P pin では末端の公開 predicate だけを patch する。

## 4. 量化縮退との対応

裁定正本で登録された N は `1, 2, 3, 4, 8, 63, 64`。下表の `1〜64` は、その全点を含む任意の正整数 N への一般化である。

| pin | G `successor_rows[:N]` | P `changed[:N]` |
|---|---|---|
| 層1 G | `1 ≤ N ≤ 64` を kill | kill しない。G で先に拒否 |
| 層1 P | `1 ≤ N ≤ 64` を cross-kill | `1 ≤ N ≤ 64` を kill |
| 層2 G | `1 ≤ N ≤ 64` を kill | kill しない。G で先に拒否 |
| 層2 P | `1 ≤ N ≤ 64` を cross-kill | `1 ≤ N ≤ 64` を kill |
| 正例 | G/P とも縮退 kill は目的外 | 同左 |

G pin では切られた prefix がすべて正当な +1 なので、N≤64 は最後の g1→g3 を見ずに受理する。P pin では全 65 行が changed で、N≤64 は最後の False を見ずに受理する。P pin に G 縮退を入れた場合も最後の changed row 自体が作られないため cross-kill になる。

M=65 の各 fixture では、G は `successor_rows`、P 正例/P 負例は `changed` がともに長さ65である。したがって **N≥65 は元の iterable と完全一致する equivalent mutation** であり、5 pin では殺せない。N=0 は裁定 matrix 外だが、負例では no-op 診断への変化または predicate 全省略により赤になる設計とする。

## 5. 両層の正例

5本目は `test_65_env_plus_one_is_accepted_by_loader_and_issuer` とし、現行 `_run` (`test_env_contract_activation.py:2159`) の直前へ追加する。

- loader 用 directory に serial 1/2 を置き、全65 env g1→g2を `activation.load_activation_state` で読む。
- `activation_serial == 2`、active row 数65、全 generation が2であることを assert。
- issuer 用には別 directory を使い、serial 1だけを配置する。
- 同じ合成 registry と全65個の `--active ...=2` で `issuer.main(argv) == 0` を assert。
- `00000002.json` の存在、canonical JSON + LF、row 数65、全 generation が2であることを assert。

loader と issuer の directory を分けることで、loader 正例の serial 2 が issuer の候補 filename と衝突しない。この node は量化縮退の kill 用ではなく、量化点を過剰に厳しくする実装や reject-all 変異を検出する positive control である。

## 6. 親が実走する nodeid

以下は未実走。親は直接 pytest ではなく `tools/run_tests.py ... --force-dispatch` に渡す。

```text
orchestrator/tests/test_env_contract_activation.py::test_production_loader_rejects_65th_env_generation_skip
orchestrator/tests/test_env_contract_activation.py::test_production_loader_rejects_65th_changed_env_invalid_successor
orchestrator/tests/test_env_contract_activation.py::test_issue_main_rejects_65th_env_generation_skip_without_publishing
orchestrator/tests/test_env_contract_activation.py::test_issue_main_rejects_65th_changed_env_invalid_successor_without_publishing
orchestrator/tests/test_env_contract_activation.py::test_65_env_plus_one_is_accepted_by_loader_and_issuer
```

焦点5 node 後に、同ファイル全体も実走して既存77 nodeが不変であることを確認する。

## 7. 想定コスト

- 追加行数: helper 約70〜85行、5 node 約125〜145行、合計 **約210±20行**。
- データ量: 131 `GenerationEntry`、activation record 2本×65 row。JSON は合計で数十 KiB。
- 計算量: registry 構築・G/P の走査とも O(65)。subprocess、calibration I/O、Hypothesis はない。
- pin 1本の test body は静的見積りで **10^-2 秒オーダー**。根拠は数百 object の構築、最大65回の predicate、1〜2本の小規模ファイル I/Oだけである。
- brief の全77 node実測 4.38秒には interpreter・pytest・dispatch の固定費が含まれるため、単独 dispatch の wall time は秒オーダーになり得る。増分時間は未実走であり断定しない。

## 総括

- **層1入口:** `activation.load_activation_state` を採る。正例まで `ec.current_activation_state()` に上げると65件の実 calibration 検証が必須となり、patch すれば correctness gate を迂回するため。
- **M:** 65は既存最良 frontier 63を越え、N=64まで殺す最小値なので妥当。ただしN≥65は fixture長により equivalent となり、無限族は閉じない。
- **親裁定点:** 上位 loader から leaf への catalog identity はコード上明白だが、既存 identity test は catalog を assert していない。この静的 bridge を十分とするか、第6の強化 assert を別 scopeで許可するかは親が裁定すべきである。