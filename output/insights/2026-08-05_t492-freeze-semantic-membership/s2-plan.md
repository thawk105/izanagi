# T-492 実装プラン v1

結論は、生成時の `_trigger_entries()` と、文書受理時の `_validate_schema()` の二点から同じ membership helper を呼ぶ構成とする。`verify_document()` 内だけに検査を置く案では、T-080 active 時の S8b 公開 gate を覆えない。

以下は静的調査に基づくプランであり、実装・pytest 実走は行っていない。

## 編集点

### 1. canonical predicate 権威の import

`orchestrator/campaign/s1_known_axes_freeze.py:24-27` の既存 campaign import 群の後に追加する。

```python
from campaign import trigger_gate_binding  # noqa: E402
```

関数だけを再実装せず、`trigger_gate_binding.is_canonical_predicate()` を名前空間付きで呼ぶ。

循環 import はない。

- `s1_known_axes_freeze.py:24-27` は `axis_trigger_gating`、各 sweep、`campaign.pipeline` の順で import する。実際には `backoff_sweep.py:36` や `s8a_trigger_sweep.py:73-90` が先に `pipeline` をロードする。
- `pipeline.py:49-56` は `axis_trigger_gating` → `reflux_ir` → `trigger_gate_binding` の順。
- `trigger_gate_binding.py:11` は `.reflux_ir` のみを import し、`reflux_ir.py:8` は `.axis_trigger_gating` を import する。
- `pipeline` または `s1_known_axes_freeze` へ戻る edge はない。新 import を現行 `pipeline` import 後に置けば、通常は既にロード済みの module を取得するだけである。

### 2. 共通 membership helper

`orchestrator/campaign/s1_known_axes_freeze.py:77-80`、`FreezeError` 直後へ次の署名を追加する。

```python
def _require_canonical_trigger_predicate(
    predicate: object, *,
    workload: str,
    configuration: str,
) -> None:
```

契約は次のとおり。

- `predicate` をそのまま `trigger_gate_binding.is_canonical_predicate()` に渡す。
- `False` なら、述語本文を診断へ転載せず `FreezeError` を投げる。診断案は  
  `entries.{workload}.{configuration}.gate_predicate が正準集合外`。
- 戻り値や正規化済み文字列は返さない。入力も書き換えない。
- `canonicalize_predicate()` や独自の空白処理は使わない。

権威集合は `trigger_gate_binding.py:97-100` が `range(32)` の emitter 出力から作り、判定は同ファイル `:113-115` の `type(text) is str and text.strip() in CANONICAL_PREDICATES` である。

### 3. 生成層

`orchestrator/campaign/s1_known_axes_freeze.py:_trigger_entries()` の以下へ挿入する。

- 現行 `:493` の `gate_predicate` 取得直後、`:494` の main/remeasure 完全一致検査より前。
- 現行 `:496` の `ident_predicate` 取得直後、`:497` の完全一致検査より前。

それぞれ次を渡す。

- system gate: `predicate=gate_predicate`, `workload=workload`, `configuration="system_gate"`
- ident: `predicate=ident_predicate`, `workload=workload`, `configuration="ident_all"`

remeasure 側を membership 検査し、現行 `:494-498` の byte-exact equality を残すことで main 側も同一値に束縛する。片側 drift は従来の不一致で、両側連動 drift は新 membership で拒否される。

### 4. 検証層

`orchestrator/campaign/s1_known_axes_freeze.py:_validate_schema()` の現行 `:700-715`、workload/entry 構造検査後に、各 workload の `system_gate` と `ident_all` を走査する。

- record が `Mapping` でなければ `FreezeError`。
- `record.get("gate_predicate")` を共通 helper へ渡す。
- 対象は厳密に 3 workload × 2 configuration の6値。`sort_best.comparator` と backoff は触らない。

`verify_document()` は `:720` で最初に `_validate_schema(doc)` を呼ぶため、文書自身を再構成前に拒否できる。また、この配置なら後述の T-080 static adapter も追加編集なしで同じ検査を利用する。

## 生成層と検証層の被覆判定

build 側一か所だけでは不足する。

| consumer | 実コード上の経路 | 結論 |
|---|---|---|
| `s1_known_axes_freeze.verify_document` | `:759-764` で `build_document()` を再実行 | 通常経路では `_trigger_entries()` の検査も通るが、それだけに依存しない。doc 検査を `:720` の `_validate_schema()` に置く。 |
| `s1_verify_extime_calibration.validated_target` | `:197-204` で `verify_fn` を差し替え可能 | no-op verifier は `verify_document` 内の検査も迂回する。ただし consumer 自身が `:216-224` で frozen/target の一致後に canonical sink gate を持ち、使用する read-heavy system gate 一値を拒否する。 |
| `s1_measurement_freeze._verify_known_axes` | `:156-163` で `known_axes.verify_document()` を直接呼ぶ。`verify_fn` 注入はない | 通常の build 再構成と新 `_validate_schema()` の両方を通る。`build_document()` と measurement verify の入口は `:249`、`:407-439`。 |
| `s8b_oracle_driver` legacy | `:406-419` で `adapter_refusals is None` の場合のみ `s1_known_axes_freeze.verify()` | legacy なら build 側でも覆える。 |
| `s8b_oracle_driver` T-080 active | `:161-230` の static adapter を使い、`:406` で legacy verify を完全に飛ばす | build 側は発火しない。`t080_freeze_migration.py:2084` → `_verify_known_schema():1803-1814` → `known_module._validate_schema()` の経路を使うため、doc 検査は `_validate_schema()` に置く必要がある。 |

両検査が単独で殺す入力例は次のとおり。

- 生成層だけ: main と remeasure の `g_rl.implementation` をともに `"izanagi_gate_pass = true;"` にする。現行 equality は通るが `_trigger_entries()` が文書構築前に拒否する。
- 検証層だけ: otherwise-valid doc の `entries.balanced.ident_all.gate_predicate` だけを同じ非正準文へ変え、`_validate_schema()` へ直接渡す。provenance/build を一度も呼ばず拒否する。

`generate()` は `s1_known_axes_freeze.py:769-779` で `build_document()` の結果を直接書き、verify/schema を呼ばないため、生成層の独立検査も必要である。

## 受理集合

変更前は、生成時には predicate が文字列で main/remeasure 完全一致なら、32述語集合外でも通り得た。通常 verify の単純な doc 改竄は再構成等値で拒否されるが、producer と両 provenance が同時に drift すれば再構成も同じ非正準文を生成できた。

変更後は次の積集合になる。

```text
生成後受理集合 = 従来の生成受理集合 ∩ 6値すべての canonical membership
検証後受理集合 = 従来の検証受理集合 ∩ doc内6値すべての canonical membership
```

したがって受理集合は拡大しない。既存の source hash、generator hash、main/remeasure equality、pairing、再構成等値も一切削らない。

現行 artifact の静的照合結果は以下の6値すべてが emitter bytes と exact 一致し、`.strip()` も不要だった。

- balanced: `system_gate=g_rl/mask 8`、`ident_all/mask 31`
- write-heavy: `system_gate=g_rt/mask 4`、`ident_all/mask 31`
- read-heavy: `system_gate=g_rl/mask 8`、`ident_all/mask 31`

`test_reflux_ir.py:445-460` も同じ6 record・3 mask・byte-exact 関係を固定している。外側空白付き emitter 文は既存権威どおり受理するが、元文字列は書き換えない。

## テスト計画

`test_s1_known_axes_freeze.py:42-50` の helper 群付近へ、pytest fixture を要求しない test helper を追加する。末尾の独自 runner `:265-292` は `tmp_path` しか注入しないため、patch には `unittest.mock` を使う。

追加 nodeid 案:

- 正例

  - `orchestrator/tests/test_s1_known_axes_freeze.py::test_current_six_frozen_trigger_predicates_pass_semantic_membership`  
    現行 JSON を読み、6値を数えて `_validate_schema()` が通ることを固定する。

  - `...::test_trigger_entries_accepts_current_six_canonical_predicates`  
    現行6値から main/remeasure 同一の synthetic provenance を作り、`_campaign_file`、`_load_json`、source builder だけを mock して、3 workload の `_trigger_entries()` が同じ述語を返すことを確認する。

  - `...::test_schema_membership_preserves_authoritative_outer_strip_equivalence`  
    emitter 文の外側だけに空白を付けて `_validate_schema()` が受理し、値を書き換えないことを確認する。

- 生成層だけの負例

  - `...::test_trigger_entries_rejects_coordinated_noncanonical_system_gate`
  - `...::test_trigger_entries_rejects_coordinated_noncanonical_ident_all`

  各 test は3 workload を走査し、main/remeasure の対象値をともに `"izanagi_gate_pass = true;"` にする。doc verifier は呼ばない。

- 検証層だけの負例

  - `...::test_validate_schema_rejects_noncanonical_system_gate`
  - `...::test_validate_schema_rejects_noncanonical_ident_all`

  現行 doc の各 workload を一つずつ deep-copy して対象値だけを変え、`_validate_schema()` を直接呼ぶ。生成・再構成・hash 検査は呼ばない。

  - `...::test_verify_document_rejects_noncanonical_predicate_before_rebuild`  
    `build_document` を「呼ばれたら失敗」の sentinel に差し替え、`verify_document()` が最初の `_validate_schema()` で `FreezeError` になることを配線テストする。

既存の以下は緩めず、そのまま回帰対象に残す。

- `test_reflux_ir.py::test_frozen_gate_predicates_match_six_records_with_three_distinct_masks`
- `test_trigger_gate_binding.py::test_canonical_predicate_membership_is_exact_after_outer_strip`
- `test_s1_verify_extime_calibration.py::test_validated_target_accepts_all_32_canonical_predicates`
- 同ファイルの matching/noncanonical 拒否2本
- `test_s1_known_axes_freeze.py` の source、generator、再構成、pairing 改竄テスト

## 既存の赤1本への対処

対象は `test_s8b_oracle_driver.py:2694-2743`。

P3 の「historical bytes を使う」方向は正しいが、stub repo へコピーするだけでは不足する。known-axes verifier は `s1_known_axes_freeze.py:724` で `source_resolver` ではなく module-global `ROOT / SCRIPT_REL` を hash するため、現在の test process では host worktree の編集済み generator を見る。

採用案は次の補正版とする。

1. 現行 `historical_bytes():2700-2711` をそのまま再利用する。
2. stub の known-axes JSON を読み、`known["generator"]["path"]` へ、同 record の SHA-256 と一致する historical bytes を replay する。
3. `driver.gate_check():2725-2727` の間だけ `mock.patch.object(driver.s1_known_axes_freeze, "ROOT", root)` を適用し、実 verifier がその replay bytes を hash するようにする。
4. holdout generator の意図的 tamper、refusal 4件、known source mismatch 1件という `:2717-2743` の期待値は一字も緩めない。

これにより test は「holdout generator の意図的改竄が公開 gate に届く」「known leg は historical generator drift ではなく既存 source drift で拒否される」という元の意図を保持する。別案として gate 全体を stub repo import の隔離 subprocess で実行できるが、この一本には上記の test-local `ROOT` 束縛の方が小さい。

## 変異事前登録候補

| 検査点 | 無効化変異 | 赤になる予定 nodeid | 一意性 |
|---|---|---|---|
| `_trigger_entries()` の system gate call | helper 呼出し削除 | `test_trigger_entries_rejects_coordinated_noncanonical_system_gate` | 登録可。type と equality は通る synthetic input で、doc 層を呼ばない。失敗理由は `FreezeError` 不発だけ。 |
| `_trigger_entries()` の ident call | helper 呼出し削除 | `test_trigger_entries_rejects_coordinated_noncanonical_ident_all` | 登録可。同上。 |
| `_validate_schema()` の6値走査 | helper 呼出し削除、または configuration を一方省略 | `test_validate_schema_rejects_noncanonical_system_gate` / `...ident_all` | 登録可。直接 `_validate_schema()` だけを呼ぶため、前後の hash・再構成・生成層に拒否されない。 |
| 共通 helper 本体を恒真化 | `is_canonical_predicate` 結果を無視 | 上記生成・検証の複数 node | 登録しない。両 inspection point を同時に殺し、call-site の局在を判別できない。 |
| public `verify_document` 配線 test | doc check 削除 | `test_verify_document_rejects_noncanonical_predicate_before_rebuild` | 事前登録しない。check が消えると generator hash／再構成も同じ doc を拒み得て、赤理由が一層に固定できない。 |

既存 `test_reflux_ir.py:445-460` は artifact-at-HEAD の pin であり、新しい call-site を削除しても緑のままなので、新検査点の mutation killer としては登録しない。

## 凍結 bytes 不変

production の変更は predicate を dict へ格納する前の拒否と、doc の読取検査だけであり、`build_document():630-679` の出力 field・順序・値を変更しない。現行6値はすべて通るため predicate bytes も変わらない。

ただし generator 自己 hash は `s1_known_axes_freeze.py:634-637` が live source bytes から計算するので、将来 `build_document()` を再実行して新規 freeze を発行すれば generator SHA は変わる。今回は `generate():769-781` を実行せず、既存 artifact を一切編集しないことが「再凍結しない」の具体的契約になる。

現在の比較基準 SHA-256 は静的取得済み。

- `output/s1-freeze/known_axes_freeze.json`: `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516`
- `output/s1-freeze/measurement_freeze.json`: `203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a`
- `output/s8b-freeze/floor_protocol.json`: `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac`
- `output/s8b-freeze/holdout_freeze.json`: `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- `output/s8b-freeze/selector_predictions.json`: `5884c83f010f73914fe121e9eb7b2fe047a4739087a984d17287cfa338fd73f1`

T-080 も `t080_freeze_migration.py:44-45` で known/holdout raw bytes をこの値へ固定し、holdout artifact 自身も `output/s8b-freeze/holdout_freeze.json:9-11` で known raw SHA を記録している。これらの定数・artifact は更新しない。

実装後は親が `git diff --exit-code -- output/s1-freeze output/s8b-freeze` と上記 SHA-256 の再計算で byte 不変を確認する。

## 総括

- 採用したプランの骨子: 共通 membership helper を `_trigger_entries()` と `_validate_schema()` の二層から呼ぶ。production 編集は `s1_known_axes_freeze.py` 一ファイルに限定し、成果物は再発行しない。
- P1: `_trigger_entries()` は生成検査点として賛成。ただし build 一点で全 verify consumer を覆うという結論は、T-080 active adapter が build/legacy verify を飛ばすため反対。
- P2: 独立 doc 検査には賛成。配置は `verify_document()` 限定ではなく、同関数と T-080 `_verify_known_schema()` の双方が使う `_validate_schema()` とする。
- P3: 条件付き賛成。historical bytes replay は意図を保つが、module-global `ROOT` も test-local stub へ束縛しない限り generator 検査には効かない。
- 残る不確実性: pytest は未実走。親が新 node、既存 freeze consumer 群、T-080 active/never-issued 経路、修正後の G7 node を計算ノードで実測し、artifact SHA 不変も確認する必要がある。