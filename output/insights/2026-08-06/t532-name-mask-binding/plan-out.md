# T-532 実装プラン v1

採用方針は「述語→mask→正準名集合」の正引きである。`name` の文法を逆パースせず、`s8a_trigger_sweep` の emitter を名前の権威として使う。変更は production 2 ファイル、test 2 ファイルに限定し、凍結成果物・凍結 source は変更しない。

## mask の導出と照合

導出経路は次のとおり。

```text
gate_predicate
  → trigger_gate_binding.mask_for_canonical_predicate()
  → predicate_mask
  → GATEABLE_REASONS の bit 順で reasons(mask)
  → s8a_trigger_sweep.subset_name(reasons)
  → その mask の正当な name 集合
  → record["name"] が集合に含まれるか検査
```

`trigger_gate_binding` の mask index は `reflux_ir.emit_predicate(TriggerGateIR(mask))` を mask 0〜31 の順に列挙して作る。これと凍結 emitter の `s8a_trigger_sweep.predicate_for(reasons(mask))` の全32点 byte 一致は、既存の `test_all_32_predicates_match_legacy_differential_oracle_byte_for_byte` が担保している。

代表値は以下となる。

| mask | reasons | 正当な name |
|---:|---|---|
| 4 | `readvali-tid` | `g_rt` |
| 8 | `readvali-locked` | `g_rl` |
| 31 | 全5要因 | `g_lc+ua+rt+rl+nv`, `ident_all` |

mask 31 は、`subset_name(all reasons)` が生成する通常名と、`candidates()` が別途追加する control 名 `ident_all` の両方を許可する。configuration 固有の名称制限までは加えない。それは name↔mask 一致を越える schema 拡張になるためである。

`stock` は `BACKOFF_TRIGGER_GATING=0` の別系統で、凍結文書では `stock_common` を含む他4 configuration に `gate_predicate` がない。検査対象は現行どおり `("system_gate", "ident_all")` のみとし、`stock` に仮想 mask を割り当てない。

現行6 record は、balanced/read-heavy の `g_rl` が mask 8、write-heavy の `g_rt` が mask 4、3つの `ident_all` が mask 31 となる。

## production の変更

### 1. `trigger_gate_binding.py`

対象: [orchestrator/campaign/trigger_gate_binding.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/trigger_gate_binding.py:13)

1. `__all__` に公開関数を追加する。

   - 位置: current lines 13–28
   - 前 anchor: `    "is_canonical_predicate",`
   - 後 anchor: `    "new_nonce",`
   - 追加: `    "mask_for_canonical_predicate",`

2. mask 順の predicate tuple と逆 index を追加する。

   - 位置: current lines 97–100
   - 前 anchor: `    return index`
   - 後 anchor: `CANONICAL_PREDICATES: frozenset[str] = frozenset(_CANONICAL_PREDICATE_INDEX)`

   現在の generator 式を次の構成へ置き換える。

   ```python
   _CANONICAL_PREDICATES_BY_MASK = tuple(
       emit_predicate(TriggerGateIR(mask)) for mask in range(32)
   )
   _CANONICAL_PREDICATE_INDEX = _build_canonical_predicate_index(
       _CANONICAL_PREDICATES_BY_MASK
   )
   _CANONICAL_PREDICATE_MASK_INDEX = {
       predicate.strip(): mask
       for mask, predicate in enumerate(_CANONICAL_PREDICATES_BY_MASK)
   }
   ```

   既存の `_build_canonical_predicate_index` を通すため、predicate 重複時の import-time 拒否は維持される。

3. 公開導出関数を新設する。

   - 位置: current lines 110–113 の間
   - 前 anchor: `    return _CANONICAL_PREDICATE_INDEX[key]`
   - 後 anchor: `def is_canonical_predicate(text: object) -> bool:`

   署名:

   ```python
   def mask_for_canonical_predicate(text: object) -> int:
   ```

   `canonicalize_predicate` と同様に exact `str` と外側 whitespace のみを受理し、index の mask を返す。非正準値は既存の一様な例外にする。

   - 例外型: `TriggerGateBindingError`
   - 診断: `invalid trigger gate binding`
   - `__context__` / `__cause__`: 既存どおり `None`

`trigger_gate_binding.py` から `s8a_trigger_sweep` は import しない。

### 2. `s1_known_axes_freeze.py`

対象: [orchestrator/campaign/s1_known_axes_freeze.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:82)

1. name↔mask 検査 helper を新設する。

   - 位置: current lines 82–89
   - 前 anchor:

     ```python
             raise FreezeError(
                 f"entries.{workload}.{configuration}.gate_predicate が正準集合外")
     ```

   - 後 anchor: `def _sha256(path: Path) -> str:`

   署名:

   ```python
   def _require_trigger_name_mask_binding(
           name: object, predicate: object, *,
           workload: str, configuration: str) -> None:
   ```

   処理順は固定する。

   1. `_require_canonical_trigger_predicate(...)` を先に呼び、既存の非正準診断を維持する。
   2. `mask_for_canonical_predicate(predicate)` で `predicate_mask` を得る。
   3. `trigger_axis.GATEABLE_REASONS` の定義順から reasons を復元する。
   4. `s8a_trigger_sweep.subset_name(reasons)` を正準名とする。
   5. mask が `(1 << len(GATEABLE_REASONS)) - 1 == 31` の場合だけ `s8a_trigger_sweep.IDENT_NAME` も許可する。
   6. name が許可集合外なら `FreezeError`。

   新しい不一致診断は次で固定する。

   ```text
   entries.{workload}.{configuration}.name と gate_predicate の mask が不一致: name={name!r} predicate_mask={predicate_mask} expected_names={expected_names!r}
   ```

   例として `g_rl` に g_rt の正準述語を付けた場合:

   ```text
   entries.balanced.system_gate.name と gate_predicate の mask が不一致: name='g_rl' predicate_mask=4 expected_names=['g_rt']
   ```

2. 生成層から helper を呼ぶ。

   - 位置: current lines 501–510
   - system_gate の前 anchor:  
     `gate_predicate = implementation(re_prov, gate_name, "remeasure")`
   - system_gate の後 anchor:  
     `if gate_predicate != implementation(main_prov, gate_name, "main"):`
   - ident_all の前 anchor:  
     `ident_predicate = implementation(re_prov, "ident_all", "remeasure")`
   - ident_all の後 anchor:  
     `if ident_predicate != implementation(main_prov, "ident_all", "main"):`

   既存の `_require_canonical_trigger_predicate` 呼出しを、新 helper に置換する。main/remeasure 完全一致検査はそのまま残す。

3. schema 層から helper を呼ぶ。

   - 位置: current lines 725–734
   - 前 anchor: `for configuration in ("system_gate", "ident_all"):`
   - 後 anchor: `generator_doc = doc.get("generator")`

   現在の canonical membership 呼出しを次の引数へ置換する。

   ```python
   _require_trigger_name_mask_binding(
       record.get("name"),
       record.get("gate_predicate"),
       workload=workload,
       configuration=configuration,
   )
   ```

通る正例:

```python
predicate = s8a_trigger_sweep.predicate_for(("readvali-locked",))
assert trigger_gate_binding.mask_for_canonical_predicate(predicate) == 8
_require_trigger_name_mask_binding(
    "g_rl", predicate,
    workload="balanced", configuration="system_gate",
)  # None
```

## テスト変更

### `test_trigger_gate_binding.py`

対象: [orchestrator/tests/test_trigger_gate_binding.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_trigger_gate_binding.py:225)

- `test_mask_for_canonical_predicate_recovers_all_32_masks`

  - 挿入 anchor 前: `assert not BINDING.is_canonical_predicate(None)`
  - 挿入 anchor 後: `@pytest.mark.parametrize("outer", _OUTER_WHITESPACE)`
  - 全32 predicate と外側 whitespace から元 mask を復元し、`__all__` への公開も確認する。
  - kill: mask index の off-by-one、bit 順入替え、`.strip()` 欠落、公開漏れ。

- `test_mask_for_canonical_predicate_rejects_nonmember_uniformly`

  - 挿入 anchor 前: `def test_canonical_json_has_stable_sorted_key_order_and_source_none():`
  - 直前の anchor: `def test_canonicalize_predicate_rejects_nonmember_with_uniform_error():`
  - 非正準文字列、bytes、`str` subclass、`None` を `_capture_rejection` で検査する。
  - kill: fail-open、暗黙 coercion、例外型・文言・cause/context の逸脱。

### `test_s1_known_axes_freeze.py`

対象: [orchestrator/tests/test_s1_known_axes_freeze.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:98)

- 既存 nodeid  
  `test_current_six_frozen_trigger_predicates_pass_semantic_membership`

  変更せず正例として再利用する。新しい `_validate_schema` 経由で現行6 record が通るため、mask 4/8/31 と `ident_all` の過剰拒否を検出する。

- `test_validate_schema_accepts_both_mask31_names`

  - 挿入 anchor 前: `def test_trigger_entries_rejects_coordinated_noncanonical_system_gate():`
  - 直前 anchor: `M._validate_schema(doc)`
  - mask 31 の predicate に対し、`g_lc+ua+rt+rl+nv` と `ident_all` の双方を別々の deepcopy で通す。
  - kill: mask 31 の一方だけを正当名とする過剰拒否、configuration 固有制限の混入。

- `test_trigger_entries_rejects_coordinated_canonical_name_mask_tamper`

  - 挿入 anchor 前: `def test_validate_schema_rejects_noncanonical_system_gate():`
  - 直前 anchor: `def test_trigger_entries_rejects_coordinated_noncanonical_ident_all():`
  - 引数なしの1 nodeid 内で3 workload × 2 configuration を回す。plain runner 契約を壊すため pytest parameter は使わない。
  - main/remeasure の両 provenance に同じ「別名の正準述語」を置き、既存 equality を通過させる。
  - kill: `_trigger_entries` の新 helper 呼出し削除、system_gate/ident_all の片側だけの検査、canonical membership のみへの退行。

- `test_validate_schema_rejects_coordinated_canonical_name_mask_tamper`

  - 挿入 anchor 前: `def test_generate_rejects_noncanonical_predicate_before_writing(tmp_path):`
  - 直前 anchor: `def test_validate_schema_rejects_noncanonical_ident_all():`
  - 現行 document を deepcopy し、同じ6ケースを `_validate_schema` へ直接渡す。
  - kill: schema 層の呼出し削除、name 無視、configuration 片側のみの検査。

既存の非正準 predicate テストは変更しない。これにより、新 helper が membership 検査より先に別診断を出す退行も赤になる。

## 単一理由性と mutation kill

- 生成層の負例は predicate を文字列・正準集合内にし、flags を維持し、main/remeasure の両方を同じ値にする。このため、新検査より前の型検査・membership・provenance equality では拒否されない。
- schema 層の負例は既存 document の keys・型を保ち、正準 predicate だけを別 mask にする。`_validate_schema` 直呼びなら前段拒否はない。
- `assert_s1b_pairing` は後段であり、`g_rl`＋g_rt predicate のように gate≠ident が保たれる改竄は拒否しない。
- 非正準 predicate は既存 membership で先に落ちるため、新しい name↔mask 検査の kill として数えない。
- T-080 の raw artifact を直接改竄する統合試験は、`known_axes.artifact_bytes` や source closure が schema より先に拒否する。その経路の赤は schema mutation の kill として数えず、上記 `_validate_schema` 直接テストを根拠にする。
- `s1_verify_extime_calibration.validated_target` 経由の read-heavy 改竄も、新 schema 検査が先に発火するようになるため、同関数固有の後段比較の kill とは区別する。

## consumer への波及

- `s1_verify_extime_calibration`: [validated_target:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_verify_extime_calibration.py:197) が最初に `verify_document` を呼ぶため、read-heavy 固有の完全一致比較より先に全6 record の schema 束縛が効く。コード変更なし。
- `s1_measurement_freeze`: [_verify_known_axes:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_measurement_freeze.py:156) から `verify_document` を呼ぶ生成・検証経路に波及し、失敗時は既存の `known_axes_freeze 照合失敗:` で包まれる。コード変更なし。
- `s8b_holdout_freeze`: known_axes を `_load_json` して射影するだけで、`s1_known_axes_freeze._validate_schema` は直接呼ばない。したがって本 module 単独には新検査は波及しない。holdout freeze は brief の scope 外なので変更しない。
- `s8b_oracle_driver`: legacy 経路の `s1_known_axes_freeze.verify` と、active receipt 経路の T-080 static adapter の双方から間接的に新検査へ到達する。コード変更なし。
- `t080_freeze_migration`: [_verify_known_schema:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/t080_freeze_migration.py:1803) が repin 投影後に `_validate_schema` を呼ぶ。本番拒否は `MigrationError("known_axes.schema", <FreezeError の文言>)` へ変換される。コード変更なし。

なお legacy `verify_document` 利用者には既存の generator SHA drift が別途存在する。新検査は `_validate_schema` でそれより前に実行されるが、legacy 全体が現在成功すると主張しない。

## provisional 裁定

- **P1: 支持。** predicate mask から `subset_name(reasons(mask))` を正引きする方が短く、`_ABBREV` 文法の重複実装を避けられる。mask 31 だけ正当名集合を2要素にする。
- **P2: 支持。** `ident_all` は mask 31 の emitter 由来 alias。`stock` と他4 configuration は `gate_predicate` がなく対象外である。
- **P3: 支持。** 生成点と `_validate_schema` が必要な2点で、後者は T-080 本番到達点から呼ばれる。ただし raw-byte tamper の統合試験では先行 hash 拒否が schema kill を覆う。
- **P4: 支持。** production 変更は `trigger_gate_binding.py` と `s1_known_axes_freeze.py` のみ。テスト2ファイルは別途追加するが、`reflux_ir.py`、凍結 source、consumer は変更しない。

pytest は実行しておらず、緑は主張しない。親の実測では Pegasus 計算ノードへ dispatch し、禁止3ファイルと凍結 JSON に diff がないことも併せて確認する。

## 総括

- 正準 predicate から mask を公開導出し、mask から emitter 正準名集合を正引きする。
- 生成層と T-080 到達可能な schema 層の双方で canonical coordinated tamper を拒否する。
- mask 31 の2名称を保ち、`stock`・他4 configuration・凍結 bytes には触れない。
- 最大の不確実性は、T-080 の先行 raw-hash 拒否により end-to-end mutation attribution ができない点である。