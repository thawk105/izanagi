静的再レビューの判定は **NO-GO** です。production 実装自体には新たな fail-open を認めませんが、全 node を通る誤実装が3系統残り、変異事前登録にも未修正の must-fix が1件あります。

本レビューでは pytest、素の Python runner、import、mutation harness を一切実走していません。親報告の **199 passed** は既知情報として扱い、以下は `git diff` とソースの静的読解による判定です。

## 所見対応表

| 所見 | 状態 | 深刻度 | 根拠 (file:line) | 成果物影響 | 修正案 |
|---|---|---:|---|---|---|
| レンズC-1 terminal serial assert消失 | closed | 解消済み must-fix | [`assert state.activation_serial == 3`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:568>) を復元。 | staleなterminal serialを再び検出できる。 | 現nodeを維持。 |
| レンズC-2 `first_failure`消去 | partial | **must-fix** | False→Trueは[816–831](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:816>)、非bool／例外は単独入力のみ[887–907](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:887>)。 | 先行する非boolまたは例外を後続成功で消す退行が不正edgeを受理する。 | 非bool→True、例外→Trueを独立node化。 |
| レンズC-3 transition内env集合検査の到達不能 | closed | nit | production precondition／defense-in-depthが[266–268](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:266>)、外側所有者が[test docstring](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:1103>)に明記された。 | 受理集合は不変で、検査所有者の誤認が解消した。 | なし。 |
| レンズD-1 adapter返り値破棄 | closed | 解消済み must-fix | 同じ実物pegasus g1→g2にFalseを注入し、adapterとloader双方を拒否させる[931–968](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:931>)。 | row値だけの別量で再判定するadapterを検出できる。 | 現nodeを維持。 |
| レンズD-2 2-env固定の集約・量化 | partial | **must-fix** | 3-env正例・全行列・3件目Falseは追加済み[532–544](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:532>), [644–687](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:644>), [789–813](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:789>)。最大件数は依然3。 | 4番目以降の不正successor受理、または4-env正例の過剰拒否を見逃す。 | 4-env正例、4件目downgrade、4件目Falseを追加。 |
| レンズD-3 generation/hash片座標判定 | partial | **must-fix** | generation-onlyはprivate負例[718–740](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:718>)が殺す。一方hash-only側はpredicateが常にTrueでcall traceだけを検査[690–715](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:690>)。 | generation変更を観測だけして判定結果を捨てるgateが不正edgeを受理する。 | hash再利用edgeでpredicate Falseの負例と、他env据置の単独正例を追加。 |
| レンズD-4 M2/M4 kill帰属 | partial | **must-fix** | 段4は現在もM2に`(+2,-1)`、M4にN4をkillとして記載[139–142](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s4-adjudication.md:139>)。DW-M03は診断・call traceだけの赤をkillに数えない[16–20](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/docs/dev-wave/mutation.md:16>)。 | mutation台帳がmask／観測pinをsemantic killとして誤認する。 | 下記の正しいkill集合をerratumまたは実行specへ反映。 |
| レンズD-5 M6/M7/M9 anchor未具体化 | partial | should-fix | hash断片は2箇所[411,538](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:411>)、predicate annotationは3箇所[262,335,482](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:262>)、M9はmulti-site必須。 | 注入なし・別site変異を正しいmutation結果として記録し得る。 | 下記の逐語anchorをcount=1で累積適用。 |
| レンズD-6 killと観測pinの混同 | partial | should-fix | N11はmissing/extraを一nodeで処理[1103–1139](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:1103>)。N4も段4ではkill扱いのまま。 | mutation kill数が診断文字列・call traceの変化で水増しされる。 | N4等をsensitivity pinへ分離し、N11 missing/extraを別node化。 |

`regressed` と判定する所見はありません。

## 残穴の再攻撃

| 誤実装 | 静的結果 | 検出／生存理由 |
|---|---|---|
| adapterが返り値を捨て、`clocks_per_us`等で判定 | 殺される | 同一row入力でTrue/Falseを切り替える[adapter nodes](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:910>)のFalse側で赤。 |
| 旧 `changed[:2]` | 殺される | 3件目False nodeで受理して赤。 |
| `changed[:3]` | **全現行nodeを通過** | 現行fixtureの最大changed数が3。 |
| 3件までしか許さない集約 | **全現行nodeを通過** | 3-env全行列とは等価だが4-env正例を拒否できる。 |
| literalなgeneration-only分類 | 殺される | same-generation/hash差替えprivate nodeが赤。 |
| literalなhash-only分類 | call-traceで赤 | hash再利用nodeのcallback列が不足する。ただし下記の返り値破棄変種は生存。 |
| 全failureを後続Trueで消す | 殺される | False→True nodeが赤。 |
| 例外だけを後続Trueで消す | **全現行nodeを通過** | 複数envの例外→Trueが存在しない。 |
| `predecessor.generation != 1`を拒否 | 殺される | g2→g3正例[565–572](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:565>)が赤。 |

### must-fix 1: 3件境界の量化・集約縮退

次の各誤実装は、現在の全nodeを静的には通過します。

```python
# 4件目以降の数値条件を見ない
valid_generation_transition = all(
    successor.generation == predecessor.generation + 1
    for predecessor, successor in changed[:3]
)

# 1〜3件では正しいが、4件同時+1を過剰拒否
deltas = tuple(
    successor.generation - predecessor.generation
    for predecessor, successor in changed
)
valid_generation_transition = (
    min(deltas) == 1
    and max(deltas) == 1
    and sum(deltas) in {1, 2, 3}
)

# 4件目のpredicate結果を捨てる
for predecessor, successor in changed[:3]:
    result = is_valid_registered_successor(predecessor, successor)
    ...
```

- 深刻度: **must-fix**
- 根拠: fixture上限は`THREE_ENV_CATALOG`の3 env [60–63](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:60>)。
- 成果物影響: 4環境目のdowngrade／不正successorを受理するか、正当な4環境同時+1を拒否する。
- 修正案:
  - `test_transition_accepts_four_env_simultaneous_plus_one`
  - `test_transition_rejects_fourth_env_downgrade`
  - `test_transition_rejects_when_fourth_changed_env_successor_is_false`

### must-fix 2: hash-only分類＋観測用dummy call

現在のhash再利用nodeは、callbackを呼んだ事実だけを固定しています。次の実装はそのcall列を満たしながら返り値を捨てます。

```python
if predecessor.contract_sha256 == successor.contract_sha256:
    if predecessor.generation != successor.generation:
        is_valid_registered_successor(
            predecessor,
            successor,
        )  # 誤り: call-trace用に呼ぶだけで返り値を捨てる
    continue
```

既存fixtureではenv-bも通常前進するためno-op拒否にも掛からず、state `(2, 2)` とcall列の双方を満たします。

- 深刻度: **must-fix**
- 根拠: hash再利用nodeのpredicateは常にTrue [702–704](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:702>)。
- 成果物影響: generationだけ進んだrowのsuccessor否定を無視し、不正contract参照をcurrentへ流す。
- 修正案:
  - `test_transition_rejects_generation_change_with_reused_hash_when_successor_is_false`
  - `test_transition_accepts_generation_change_when_hash_is_reused_and_other_env_is_unchanged`

### must-fix 3: failure種別限定の後続成功消去

次の退行はFalse→True nodeを通過し、単独例外nodeも通過します。

```python
elif result is True:
    if first_failure is not None and first_failure[1] is not None:
        first_failure = None  # 誤り: 先行callback例外を「回復」扱い
```

同様に、メッセージ種別を見て非bool失敗だけを消す変種も生存します。

- 深刻度: **must-fix**
- 根拠: 複数envの先頭失敗nodeはFalseだけ[816–831](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:816>)。
- 成果物影響: 先行envの例外／非bool判定を後続成功で消し、不完全に検証されたactivation edgeを受理する。
- 修正案:
  - `test_transition_preserves_first_non_bool_failure_when_later_successor_is_true`
  - `test_transition_preserves_first_exception_when_later_successor_is_true`

## regression検査

### assert・skip・xfail

fix前snapshotと現行patchの比較では、**fix1で消えたassertは0件**です。逆にterminal serial assertが追加されています。

HEADからwave全体で文字列上消えたassertは次のとおりです。

- `HEAD:test_env_contract_activation.py:488` の `assert head is not None`
  - `_chain` helperへの再構成で消滅。production期待値ではない。
- `HEAD:...:490` の `assert state.activation_serial == 4`
  - 現在は正当な3-record chainに対する `== 3` へ復元済み。
- `HEAD:...:491` の先頭row generation `== 2`
  - terminal全rowの `(3, 1)` exact assertへ強化済み。
- downgrade正例のcurrent g1／historical g2 assertions（`HEAD:...:668–675`）
  - downgrade禁止に伴い、forward current g2／historical g1 assertionsへ再構成[1313–1330](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:1313>)。

旧ever-active集合assertは[570–572](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:570>)に残っています。skip／xfailの追加、既存assertの緩和はありません。suffix rejectionの例外matchはむしろhead不一致へ強化されています[1208–1211](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:1208>)。

### production受理集合

新たな fail-open は認めません。

- transitionはpair単位のexact変更判定、exactly +1、no-op拒否、全changed callback、exact bool、例外fail-closedを保持[274–328](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:274>)。
- adapterはgeneration/env/hashをすべて解決し、`is_valid_successor`の結果を直接返す[395–432](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:395>)。
- production loaderとissuerはいずれも同じadapterを渡す[524–530](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:524>), [206–212](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/tools/issue_env_contract_activation.py:206>)。
- 変更は指定4ファイルだけで、既存production拒否条件の削除はありません。serial 2以降の受理集合は狭まり、広がっていません。

### 二重runner・oracle・診断payload

- `test_campaign.py`はHEADとbyte-identicalです。pytest任意import[33–38](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_campaign.py:33>)と素Python runner[7568–7592](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_campaign.py:7568>)に静的な波及はありません。
- activation leafのruntime importはstdlibのみ[5–12](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:5>)。
- 3-env matrixの期待値はD228式をテスト内で直接計算[658–666](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:658>)し、productionをoracleにしていません。
- clocks差nodeはproduction predicateを観測しますが、root causeは独立したFalse monkeypatch nodeでも固定されているため循環依存ではありません。
- working-tree commit/hash等の揮発値は期待値にありません。生成record自身のstate hashとchecked-in初期authorityのgoldenだけです。
- `git diff --check`は成功しました。

## M1〜M10 再登録監査

| ID | 一意性 | 正しい期待赤 | mask判定 |
|---|---|---|---|
| M1 | `if not changed:`は1箇所 | `test_transition_rejects_all_env_noop`, `test_transition_rejects_noop_in_middle_of_chain`, `test_issue_main_rejects_noop_without_publishing`, 両matrix | maskなし |
| M2 | 数値条件は1箇所 | `test_transition_rejects_skip_even_when_successor_predicate_accepts`, `test_transition_rejects_skip_when_catalog_order_is_not_generation_order`, 両matrix、same-generation/hash private node | `test_transition_rejects_compensating_plus_two_minus_one`はdowngradeにmaskされ、killではない |
| M3 | M2と同じanchorを別走行 | skip、downgrade、両compensating、両matrix、catalog-order、same-generation/hash private node | maskなし |
| M4 | callback loopは1箇所 | semantic killはsecond-Falseとthird-False | N4、hash再利用call列、first-failure call列は観測pin |
| M5 | adapter return blockは1箇所 | False monkeypatch node、resolved-invalid-contract node | 数値gateは通るためmaskなし |
| M6 | 完全条件blockなら1箇所 | `test_production_successor_adapter_rejects_rows_that_do_not_resolve` | direct adapter呼出しなので外側registryにmaskされない |
| M7 | 3-site累積置換 | `test_validate_activation_records_requires_successor_predicate` | serial 1 fixtureなのでtransitionにmaskされない |
| M8 | exact-bool blockは1箇所 | `test_transition_rejects_non_bool_successor_result` | False診断を維持する変異にすれば単一理由 |
| M9 | 3-site累積置換 | `test_transition_rejects_skip_when_catalog_order_is_not_generation_order` | private直接nodeには数値fallbackを残し、署名変更赤を避ける |
| M10 | `changed.append(...)`は1箇所 | `test_transition_accepts_three_record_forward_chain`、両matrix | 正例なのでmaskなし |

### 指定された逐語anchor

M2（[env_contract_activation.py:285](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:285>)、1件）:

```python
        if successor.generation != predecessor.generation + 1:
```

置換後:

```python
        if successor.generation < predecessor.generation:
```

`(+2,-1)`は後半の`-1`で引き続き拒否されるため期待killから外します。

M4（[env_contract_activation.py:300](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:300>)、1件）:

```python
    for predecessor, successor in changed:
```

置換後:

```python
    for predecessor, successor in changed[:1]:
```

semantic killはsecond-False／third-False。N4は観測pinです。

M6（[env_contract.py:408](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:408>)、この完全blockは1件）:

```python
    if (
        entry.generation != row.generation
        or entry.contract.env_tag != row.env_tag
        or entry.contract.contract_sha256 != row.contract_sha256
    ):
```

最後のhash条件を除去します。比較断片だけでは[post-load再照合](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:538>)にも一致するため不可です。期待killは`test_production_successor_adapter_rejects_rows_that_do_not_resolve`です。

M7はannotation単体が3件あるため、次の3つを別々の累積anchorにします。

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

```python
def load_activation_state(
    directory: Path,
    *,
    registered_contracts: Mapping[str, tuple[tuple[int, str], ...]],
    is_valid_registered_successor: _RegisteredSuccessorPredicate,
    expected_head_serial: int,
    expected_head_state_sha256: str,
) -> ActivationState:
```

```python
    if not callable(is_valid_registered_successor):
        raise ActivationRecordError(
            "is_valid_registered_successor は callable でなければならない"
        )
```

両public署名を`_RegisteredSuccessorPredicate | None = None`へ変更し、guardを`None`なら常時True predicateへ置換します。private gate署名は変更不要です。期待killは`test_validate_activation_records_requires_successor_predicate`です。

M9は単一siteでは実装不能です。次の3 blockを累積anchorにします。

```python
def _validate_activation_transition(
    predecessor_rows: tuple[ActiveContract, ...],
    successor_rows: tuple[ActiveContract, ...],
    *,
    activation_serial: int,
    is_valid_registered_successor: _RegisteredSuccessorPredicate,
) -> None:
```

```python
        if successor.generation != predecessor.generation + 1:
            raise ActivationRecordError(
                "activation generation 遷移が exactly +1 でない: "
                f"serial={activation_serial} env_tag={successor.env_tag} "
                f"g{predecessor.generation} -> g{successor.generation}"
            )
```

```python
            _validate_activation_transition(
                previous_rows,
                rows,
                activation_serial=serial,
                is_valid_registered_successor=is_valid_registered_successor,
            )
```

private gateへoptionalなcatalog indexを追加し、validator経路だけordinal比較を使い、private直接呼出しでは現行数値判定へfallbackさせます。期待killは`test_transition_rejects_skip_when_catalog_order_is_not_generation_order`だけです。

### must-fix 4: 事前登録erratum未反映

- 深刻度: **must-fix**
- 根拠: 段4のM2/M4記述が現在も旧内容のまま[139–142](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s4-adjudication.md:139>)。
- 成果物影響: maskされた`(+2,-1)`と受理集合不変のN4をkillとして記録し、mutation証拠を過大評価する。
- 修正案: 段4を履歴として保持するなら、mutation実走前に上記表を明示的なerratum／実行specへ固定する。

## 総括

**判定: NO-GO**

**must-fix: 4件**

production実装そのものは静的にはfail-closedで、受理集合の不当な拡大や新規regressionは見つかりませんでした。しかし、4-env境界、hash-only＋返り値破棄、failure種別限定の消去という3つの誤実装が現行全nodeを通過し、M2/M4の変異帰属も未修正です。pytest、素Python runner、mutationは本レビューでは実走していません。