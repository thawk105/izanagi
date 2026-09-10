結論は **GO** です。単位 1 と、production 結線を一切持たない単位 2 は今日 land できます。ただし、親 brief の「成果物影響ゼロ」は code identity まで含めると不正確なので、後述の限定が必要です。

## 1. GO / NO-GO と裁定境界

### D176 が許している範囲

[D176 の決定本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:8666) は逐語で次のとおりです。

> 実行環境契約に immutable な世代列 (`GENERATIONS`)、`contract_sha256` の逆引き (`resolve_by_contract_sha256`)、遷移述語 (`is_valid_successor`)、候補 mapping の純関数 validator (`validate_generations`) を置く。ただし各 env の世代列の長さがちょうど 1 であることを production 初期化時に要求する bootstrap fuse を同時に課し、活性化権限 (activation record / activation receipt) が実装されるまで 2 世代目の登録を fail-closed で拒否する。

[D176「射程」](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:8691) は次のように明記しています。

> 世代列が 1 本しかない間、隣接遷移の検査は production では一度も発火しない。純関数として test からのみ発火する。

> fuse は **source bootstrap の防壁**であって runtime の活性化権限ではない。逆引き index は module 属性として再束縛可能であり、authority として扱ってはならない。

したがって、D176 は「data-layer の純関数を test-only で先行配置する」形を認めています。ただし、これだけで任意の activation predicate を自動承認するわけではなく、T-624 の直接根拠は後続裁定です。

### D196 と B(a) が禁止する範囲

[D196 の決定本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:9492) の主語は逐語で限定されています。

> 契約世代の活性化権限 (activation record からの権威導出と全入口の activation receipt) を実装する前に、artifact に記録された contract hash から世代を解決する historical resolver と versioned predicate dispatch を production consumer へ配線する。D176 の bootstrap fuse はそれまで外さない。

つまり禁止対象は、record を authority にすること、receipt を入口へ配線すること、fuse を外すことです。before/after mapping を受け取って bool を返す未結線の純関数は、この列挙に含まれません。

前 wave の[択一 B(a)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/insights/2026-08-07_t529-activation-impl/s4-adjudication.md:57) は逐語で次のとおりです。

> **`DW-G04` を T-529 に限り上書きするか。** (a) 上書きせず、正規 g2 を取得できるまで設計メモに留める / (b) 合成 g2 (temp commit) の正例を発火証拠と認めて実装を進める

これは明示的に「T-529 に限り」であり、T-529 の activation authority 実装を設計メモに留める裁定です。

一方、再起票 wave の[R6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/insights/2026-08-07_t529-impl-reraise/s4-adjudication.md:43) は次のとおりです。

> 裁定 D の文言「各 env は据置または +1」だけでは全 env 据置の no-op record を拒否できない。前 wave の s4 表は no-op を明示的に問題としていたので、文言と意図に差がある。**採用。ユーザー再裁定へ返す (親が独断で条件を足さない)。**

同じ文書の[不採用理由](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/insights/2026-08-07_t529-impl-reraise/s4-adjudication.md:59) はさらに限定的です。

> レンズ B の「D も純 data-layer 述語として実装候補」は不採用 (scope 外)。R6 のとおり裁定文言に穴がある状態で predicate を land すると、「no-op を拒否する保証がある」と誤読されうる弱い gate を台帳へ残す。**ユーザー再裁定後に実装する。**

その再裁定は既に成立しています。[worklog の確定本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/worklog.md:2721) は逐語で、

> [T-624] **P2・裁定済み (2026-08-07 /rulings、(a)) → 実装可**: activation record の世代遷移規則を「全 env の delta ∈ {0,1} かつ少なくとも 1 env の delta == 1」へ明文化し、全 env 据置の no-op record を拒否する

としています。

以上から、単位 2 は GO です。ただし、consumer 呼出し、record schema、authority、receipt、fuse 除去、g2 登録のいずれかを diff に含めた時点で単位 2 は NO-GO に戻し、単位 1 の decisions 明文化だけを land します。

### 親 brief (P2) の訂正点

「新述語の production call consumer が 0」「既存 artifact bytes を変更しない」は正しいです。しかし `env_contract.py` の source bytes 自体は identity 閉包に含まれるため、次回生成する T-126 `code_identity` / `series_identity` と silo の `runtime_modules_sha256` は変わります。

したがって「既存の certified 選択・report・台帳 bytes は不変」までは正しいものの、「今後生成される identity field も含め全値不変」とは書かないでください。この訂正は GO を覆しません。

## 2. 述語の署名・配置・名前

基準 `bb824d8b` の [env_contract.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:228)、既存 `is_valid_successor` の直後、`_build_registry` の直前へ置きます。

```python
def is_valid_activation_mapping_transition(
    before: Mapping[str, int],
    after: Mapping[str, int],
) -> bool:
```

名前を `is_valid_activation_mapping_transition` とする理由は次のとおりです。

- `activation_state` を使わない。D197 の state は serial・直前 hash を含む状態全体であり、本述語はその一部分である env→generation mapping しか見ないためです。
- 既存 `is_valid_successor` は contract object 間の calibration pointer 変更を意味しており、同名・overload にしません。
- serialized field を追加しないため、D197 が禁じる無修飾 `generation` field や `migration_epoch` / `bundle_hash` も導入しません。
- `Mapping` は既に [env_contract.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:27) で import 済みです。import 行は変更不要です。

docstring には最低限、次を明記します。

> activation record の env→generation mapping 間の遷移だけを判定する。これは data であって権限ではない。issuer の型 gate や活性化権限に使わない。

実装順は次のとおりです。

1. 両引数が `Mapping` でなければ `False`。
2. key 列を materialize し、空集合、非 exact-`str` key、key 集合不一致を `False`。
3. 各 before/after 値が exact-`int` かつ正整数でなければ `False`。
4. 各 delta が `0` または `1` でなければ `False`。
5. delta `1` を一つ以上見た場合だけ `True`。

静的検索は exact word、hidden file を含み `.git` を除外して実施しました。

| 検索語 | repo 全体 | `*.py` |
|---|---:|---:|
| `is_valid_activation_mapping_transition` | 0 | 0 |
| `activation_mapping` | 0 | 0 |
| `is_valid_activation_state_transition` | 0 | 0 |
| `is_valid_successor` | 80 | 7 |
| `activation_serial` | 22 | 0 |
| `activation_state_sha256` | 17 | 0 |
| `previous_activation_state_sha256` | 8 | 0 |
| `ActivationRecord` / `activation_record` | 2 / 1 | 0 / 0 |

また、`env_contract` の wildcard import は 0 件、`__all__` もありません。新 public symbol の追加で既存 import 集合が暗黙に変わる箇所はありません。

## 3. 受理・拒否の全表

受理条件は次の論理積に固定します。

```text
before と after が Mapping
∧ keys(before) == keys(after) != ∅
∧ 全 key が exact str
∧ 全値が exact int かつ > 0
∧ 全 key で after[key] - before[key] ∈ {0, 1}
∧ 少なくとも 1 key で after[key] - before[key] == 1
```

| 分類 | 判定 | 理由 |
|---|---|---|
| 全 env 据置 | 拒否 | existential な `delta == 1` がない |
| 単一 env +1 | 受理 | 最小正例 |
| 複数 env の一部据置・一部 +1 | 受理 | 各 delta は合法で、少なくとも一つ進む |
| 複数 env 同時 +1 | 受理 | 裁定は「ちょうど一 env」へ限定していない |
| skip、+2 以上 | 拒否 | 隣接遷移でない |
| downgrade、負 delta | 拒否 | 単調性を破る |
| env 集合の追加 | 拒否 | 新 key には before 側 delta が定義できない |
| env 集合の削除 | 拒否 | 削除 key には after 側 delta が定義できない |
| 空 mapping 同士 | 拒否 | 「少なくとも一つ +1」を満たせない |
| 非 `int` 値 | 拒否 | schema/domain 外 |
| 非 `str` key | 拒否 | `Mapping[str, int]` の domain 外 |
| generation `0` 以下 | 拒否 | contract generation は正整数 |
| `dict` 以外の `Mapping` | 受理可能 | signature を exact-dict gate に狭めない |
| `bool` 値 | 拒否 | `bool` は `int` の subclass なので `type(v) is int` が必要 |
| `Mapping` でない引数 | 拒否 | bool predicate として例外を外へ漏らさない |

(P3) の「env 集合変化は拒否」は正しいです。「全 env の delta」は同じ domain 間でしか定義できません。また、現行 module は [env_contract.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:16) で静的 registry・register API なしを契約にしています。追加・削除を activation transition に混ぜると、未裁定の registry membership migration を受理集合へ持ち込むことになります。

一方、同じ synthetic `str` key 集合の存在そのものは本述語で authority 検証しません。登録済み env・実在する generation・activation chain との一致は将来 consumer 側の別 gate であり、本述語単独では保証しません。

## 4. 表駆動テスト案

[既存 successor 表の末尾](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/tests/test_env_contract.py:417) の直後、`test_validate_generations_accepts_single_generation_candidate` の前へ、次を追加します。

```python
def test_is_valid_activation_mapping_transition_table():
```

`MappingProxyType` は既に [test_env_contract.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/tests/test_env_contract.py:29) で import 済みです。

| label | before | after | 期待 |
|---|---|---|---:|
| `all-env-no-op` | `{"env-a": 1, "env-b": 4}` | `{"env-a": 1, "env-b": 4}` | `False` |
| `single-env-plus-one` | `{"env-a": 1}` | `{"env-a": 2}` | `True` |
| `mixed-stay-and-plus-one` | `{"env-a": 1, "env-b": 4}` | `{"env-a": 2, "env-b": 4}` | `True` |
| `multiple-env-plus-one` | `{"env-a": 1, "env-b": 4}` | `{"env-a": 2, "env-b": 5}` | `True` |
| `skip-plus-two` | `{"env-a": 1}` | `{"env-a": 3}` | `False` |
| `mixed-plus-one-and-skip` | `{"env-a": 1, "env-b": 1}` | `{"env-a": 2, "env-b": 3}` | `False` |
| `downgrade` | `{"env-a": 2}` | `{"env-a": 1}` | `False` |
| `mixed-plus-one-and-downgrade` | `{"env-a": 1, "env-b": 2}` | `{"env-a": 2, "env-b": 1}` | `False` |
| `env-added` | `{"env-a": 1}` | `{"env-a": 2, "env-b": 1}` | `False` |
| `env-removed` | `{"env-a": 1, "env-b": 1}` | `{"env-a": 2}` | `False` |
| `empty-mappings` | `{}` | `{}` | `False` |
| `non-int-before` | `{"env-a": "1"}` | `{"env-a": 2}` | `False` |
| `non-int-after` | `{"env-a": 1}` | `{"env-a": 2.0}` | `False` |
| `non-str-key` | `{1: 1}` | `{1: 2}` | `False` |
| `zero-generation` | `{"env-a": 0}` | `{"env-a": 1}` | `False` |
| `negative-generation` | `{"env-a": -1}` | `{"env-a": 0}` | `False` |
| `mapping-proxy-plus-one` | `MappingProxyType({"env-a": 1})` | `MappingProxyType({"env-a": 2})` | `True` |
| `bool-is-not-int` | `{"env-a": False}` | `{"env-a": True}` | `False` |
| `before-not-mapping` | `[]` | `{"env-a": 1}` | `False` |
| `after-not-mapping` | `{"env-a": 1}` | `[]` | `False` |

assert は既存慣習どおりにします。

```python
for label, before, after, expected in cases:
    assert ec.is_valid_activation_mapping_transition(before, after) is expected, label
```

変更しない既存期待値は以下です。

- `test_is_valid_successor_leaf_pointer_table`
- `test_validate_generations_synthetic_two_generation_negative_table`
- `EXPECTED_GENERATION_HASHES`
- `V2_ENV_NEUTRAL_MODULES`
- bootstrap fuse・module-level validation 順序の AST 検査
- 既存 test の assert、skip、parametrize 行

## 5. decisions へ書く D 案

canonical [docs/decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md) は直接編集しません。標準の spool 規約に従い、worklog fragment を `seq: 1` とする前提で、次を新規作成します。

`docs/spool/decisions/2026-08-07-worktree-dev-wave-t624-activation-noop-2.md`

想定配置は、1–7 行 frontmatter、9 行 H2、11 行以降本文です。

```markdown
## {{D:activation-mapping-noop-rejection}}. activation mapping は全 env 据置の no-op を拒否する
```

骨子は次のとおりです。

**決定**

- before/after の env→contract generation mapping は、同一・非空の exact-`str` key 集合を持つ。
- 全 generation は exact 正整数。
- 全 delta は `{0, 1}`、かつ少なくとも一つは `1`。
- env 追加・削除、skip、downgrade、全 env 据置を拒否する。
- `is_valid_activation_mapping_transition` はこの関係だけを表す純 data-layer 述語とする。

**理由**

- 「各 env は据置または +1」だけでは全 env 据置を受理し、serial だけ進む空の activation record を排除できない。
- skip / downgrade は隣接性・単調性を破る。
- 集合変化を許すと、未裁定の env registry migration と activation を一つの操作へ混ぜる。
- D176 の data-layer 先行方式を維持し、D196 の authority 境界を越えない。

**射程（この決定が保証しないこと）**

- 今日、新述語を呼ぶ production consumer は **0**。呼出しは表駆動 test のみ。
- 述語は権威ではなく data である。issuer、trust root、record authenticity、receipt、入口被覆を保証しない。
- `activation_serial`、`activation_state_sha256`、`previous_activation_state_sha256` の schema・連鎖を検査しない。
- mapping の env が registry 登録済みか、generation が実在するかを保証しない。
- fuse 除去、g2 登録、current 切替、historical resolver 配線を保証しない。
- 既存 artifact bytes は変えない。ただし新 commit から生成する code/runtime identity hash は source bytes に従って変わる。
- 新 env 登録時の mapping migration 規則は定義しない。

**却下した選択肢**

- `delta ∈ {0,1}` だけ — no-op を受理する。
- 全 env を必ず +1 — 合法な据置との混在を過剰拒否する。
- ちょうど一 env だけ +1 — 複数 env 同時 +1 を無断で拒否する。
- env 追加・削除を許す — registry mutation を activation に混入させる。
- exact `dict` のみ受理 — `Mapping` signature を不当に狭める。
- `isinstance(value, int)` — `bool` を generation として受理する。
- production consumer へ同時配線 — D196 / B(a) の authority 境界を越える。

## 6. 波及の静的棚卸し

| 面 | 変わる / 変わらない | 根拠 |
|---|---|---|
| 新述語の public API | **変わる** | module 属性が 1 本増える。ただし wildcard import 0、`__all__` 0 |
| 新述語の production call graph | **変わらない** | 現在の exact identifier hit は 0。consumer 配線を scope 外とする |
| `ExecutionEnvironmentContract` / `_canonical_obj` / `contract_sha256` | **変わらない** | [canonical 化](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:145) は dataclass field だけを入力とし、新関数 source を含まない |
| `GenerationEntry` / `GENERATIONS` / `REGISTRY` / index / `lookup` | **変わらない** | [module 初期化](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:342) への呼出しを追加しない |
| bootstrap fuse | **変わらない** | [validate_generations](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:316) 本文・module-level 呼出しを変更しない |
| current lookup consumer | **変わらない** | [pipeline](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/pipeline.py:36)、[T-126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/qualification/t126_driver.py:27)、[P3 gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/p3_s4_loop_trigger_gating.py:50)、[silo](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/silo_ladder_rung1.py:40)、oracle driver、floor scoping は既存 symbol だけを呼ぶ |
| historical consumer | **変わらない** | [floor](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/s8b_floor_campaign.py:90)、[ratified freeze](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/s8b_ratified_freeze.py:40)、[oracle report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/s8b_oracle_report.py:36) の resolver 呼出しを変更しない |
| type/policy consumer | **変わらない** | env attestation、execution guard、buildcache、reservation、loop は既存 class/type/lookup だけを参照 |
| T-126 code identity | **変わる** | [REQUIRED_CODE_IDENTITY_PATHS](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/qualification/contract.py:38) に `env_contract.py` が含まれ、[t126_driver.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/qualification/t126_driver.py:349) が blob SHA を計算する。新 commit の series identity は変わる |
| silo runtime binding | **変わる** | [_runtime_module_paths](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/silo_ladder_rung1.py:254) に同 file があり、[runtime_modules_sha256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/silo_ladder_rung1.py:285) が再計算される |
| 既存 historical evidence | **変わらない** | committed bytes を書き換えない。[evidence test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1249) は historical runtime binding と現行 binding が異なること自体を固定している |
| submit 済み旧 silo receipt を新 source で collect | **意図どおり拒否** | [collect drift gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/silo_ladder_rung1.py:4575) が source drift を検出する。旧 receipt を新 hash へ貼り替えない |
| `V2_ENV_NEUTRAL_MODULES` AST 検査 | **期待値不変** | `env_contract.py` は既に[対象一覧](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/tests/test_env_contract.py:82)にある。新関数へ env 固有 literal を置かず、一覧変更不要 |
| module-level validation 順序 AST | **変わらない** | 検査は固定行番号でなく AST lineno の相対順を比較する。関数追加で後続行がずれても validation→index→registry の順は不変 |
| direct source SHA pin | **変わらない** | `env_contract.py` path と 64hex を同時に固定する Python/JSON hit は静的検索で 0。binding は runtime 計算 |

親が実測する対象としては、新 node、`test_env_contract.py` 全体、silo runtime closure test、committed evidence test、T-126 identity-path test、および通常の全受入を `tools/run_tests.py` 経由で含めるべきです。本段では実走していません。

## 7. 恒真でないことの証明方針

- **無条件 `True`** は `all-env-no-op` が `False` を要求するため必ず落ちます。skip、downgrade、集合追加・削除も独立した負例です。
- **常に `False`** は `single-env-plus-one`、`mixed-stay-and-plus-one`、`multiple-env-plus-one`、`mapping-proxy-plus-one` が `True` を要求するため必ず落ちます。
- existential 条件を落とした実装は `all-env-no-op` が殺します。
- 「全 env が +1」と過剰に狭めた実装は `mixed-stay-and-plus-one` が殺します。
- `any(delta == 1)` だけを見る過剰受理は mixed skip/downgrade と env 集合変化が殺します。
- `isinstance(v, int)` の bool 漏れは `bool-is-not-int`、exact-dict 化は `mapping-proxy-plus-one` が殺します。

静的な読解・検索だけを行い、pytest は実行していません。緑は主張しません。

## 総括

- **GO**: 単位 1・単位 2 とも、純 data-layer・consumer 0 の境界内で land 可。
- 単位 1: no-op 拒否、同一 env 集合、非 authority を decisions fragment に明文化する。
- 単位 2: `is_valid_activation_mapping_transition` と正負を含む表駆動 test 1 本を追加する。
- authority / receipt / fuse / g2 / production 結線を含めた時点で単位 2 は NO-GO、単位 1 のみに戻す。
- pytest 未実行。実測と受入判定は親へ引き渡す。