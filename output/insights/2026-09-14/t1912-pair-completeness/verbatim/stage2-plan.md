## 変更面の表

**閉包外の純関数 consumer を、既存 assembler と evaluator の間に置く。** pair binding は公開済み attempt artifact から assembler が取り出した source bytes と raw bytes から再生成し、registry／manifest に突き合わせる。新しい保存先・writer は作らない。

以下の行番号は現在の worktree 基準。閉包 5 module の SHA-256 は、射影された 5 値とすべて一致した。

| 所有 path | 種別 | 追加内容・閉じる性質 |
|---|---|---|
| `orchestrator/campaign/p3_b4_pair_completeness.py` | 新設 | canonical pair binding の再生成と照合。① manifest と source 側 pair の対応、② proposal 転記、③ raw precursor、④ source identity と raw arm slot の対応を検査。receipt 重複禁止は既存関数を再利用する。 |
| `orchestrator/campaign/p3_b4_material_report.py` | 編集 | `_load_and_evaluate` の evaluator 呼出し前に必須配線。照合失敗を `B4MaterialReportError` に変換し、評価・公開へ進ませない。 |
| `orchestrator/tests/test_p3_b4_pair_completeness.py` | 新設 | 純関数の正例、性質別負例、検査を除去する変異 matrix。末尾に `raise SystemExit(pytest.main([__file__]))` を置く。自走 harness の集合は `test_plain_runner_coverage.py:44` の動的列挙に自動包含される。全 nodeid を下記所要台帳へ登録する。 |
| `orchestrator/tests/test_p3_b4_material_report.py` | 編集 | `:266` の既存 production 正例を拡張し、実 issuer／producer bytes に対する通過と、assembly 境界での変異拒否を検証。既存 node 内で行い、共有 fixture を使う新 node の分類漏れを避ける。 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 編集 | `:2` の `duration_seconds_by_nodeid` に新規テストの実測所要を追加し、`nodeid_count` を整合させる。新 test と同じ変更単位に含める。未実測値を実測として記入しない。 |

閉包 5 module、事前登録 doc、issuer、producer、rogue producer support は編集対象にしない。

## file:line 粒度のプラン

### 新設 `orchestrator/campaign/p3_b4_pair_completeness.py`

公開 API を次で固定する。

```python
def assert_b4_pair_complete(
    *,
    scheduled_registry_bytes: bytes,
    analysis_manifest_bytes: bytes,
    raw_analysis_records_bytes: bytes,
    source_artifact_bytes: tuple[bytes, ...],
) -> B4PairCompletenessReceipt:
    ...
```

入力は bytes のみ。FS、環境変数、時計、乱数、caller 指定 proposal、任意の pair manifest は受け取らない。失敗は `B4PairCompletenessError` を送出する。

closed schema は以下とする。すべて `frozen=True, slots=True` の dataclass とし、canonical payload は明示した field だけで組み立てる。

```python
@dataclass(frozen=True, slots=True)
class B4PairBindingRow:
    block_id: str
    attempt_id: str
    proposal_sha256: str
    on_precursor_hash: str
    off_precursor_hash: str
    on_source_artifact_sha256: str
    off_source_artifact_sha256: str

@dataclass(frozen=True, slots=True)
class B4PairCompletenessReceipt:
    schema_version: str
    registry_sha256: str
    manifest_sha256: str
    raw_analysis_sha256: str
    rows: tuple[B4PairBindingRow, ...]
    canonical_bytes: bytes
    sha256: str

class B4PairCompletenessError(ValueError):
    reason: B4PairCompletenessReason
    block_id: str | None
```

schema version は `p3-b4-pair-completeness/v1`。canonical JSON のトップレベル field は次の 5 個に限定する。

```text
schema_version
registry_sha256
manifest_sha256
raw_analysis_sha256
rows
```

`canonical_bytes` と `sha256` は計算結果であり、自己参照する payload には含めない。行順は manifest 順、receipt field は on/off の固定名で表す。実行順と arm 名を混同しない。

理由語彙を次に閉じる。

| enum 値 | 拒否条件 |
|---|---|
| `input_schema_invalid` | bytes／tuple／JSON／対象 schema／hash の型・値域が不正 |
| `manifest_regeneration_mismatch` | registry から凍結 manifest を厳密再生成できない |
| `source_mapping_invalid` | **既存** source digest・個数・順序・大域一意性検査が失敗 |
| `pair_manifest_mismatch` | pair の block／attempt が manifest と過不足なく対応しない |
| `proposal_registry_mismatch` | source に転記された proposal が同 attempt の registry 値と異なる |
| `precursor_registry_mismatch` | raw の on/off precursor のいずれかが registry 値と異なる |
| `receipt_arm_slot_mismatch` | raw arm が参照する source の `identity.arm` が異なる |
| `artifact_binding_mismatch` | source binding の registry／manifest hash が入力 bytes と異なる |

内部処理を以下の順にする。

1. **既存 loader と manifest 再生成を利用する。**  
   `p3_b4_analysis_ledgers.py:1140` の `assert_analysis_manifest_complete` を呼ぶ。registry 全体から attempt を参照するが、pair 母集合は manifest の選択済み 201 行だけとする。202 件以上の予定試行を持つ正例を落とさない。

2. **raw は既存 parser で読む。**  
   `p3_b4_analysis_adapter.py:390` の `parse_raw_analysis_records` を利用する。既存 raw schema に proposal field を追加しない。

3. **receipt の重複禁止を再実装しない。**  
   `p3_b4_analysis_path.py:174` の `_source_artifacts_match` を import して利用する。新 module に receipt 用 `set` 検査を複製しない。既存 evaluator 内の呼出しもそのまま残す。

4. **source bytes から照合対象だけを射影する。**  
   元 bytes の SHA-256 を使い、JSON の再シリアライズ結果を source hash に使わない。重複 JSON key、非有限数、不正 UTF-8 を拒否する。数値は binary float に変換しない。

   照合に使う既存 field は次のとおり。

   ```text
   source.schema_version
   source.identity.arm
   source.binding.attempt_id
   source.binding.block_id
   source.binding.registry_sha256
   source.binding.manifest_sha256
   source.binding.precursor_hash
   ```

   source の `binding.precursor_hash` を **pair 行の `proposal_sha256`** として読む。名称を新しい原始証拠と誤認させない。`raw.precursor_hash` とは独立に取り出す。

   source の既存形は producer `:1686`、binding は `:2027` 付近を参照する。射影外の evidence 全体を再検証する別 framework は作らない。

5. **観測行と期待行を独立に再生成する。**  
   観測行は source の block／attempt／proposal と raw の precursor／receipt から作る。期待 block／attempt／proposal は manifest と registry から作る。期待 receipt slot は source の `identity.arm` で決める。

   - raw block と両 source の block／attempt が同じ manifest 行を指すこと。
   - 観測 pair 行が manifest の 201 行と一対一であること。
   - 両 source の proposal 転記が registry の同 attempt の値に一致すること。
   - 両 raw precursor が、その **registry 値** に一致すること。
   - raw on/off の参照先が source on/off に一致すること。

   **③の比較先を、未検証の観測 proposal にしない。** ②と③を独立に検査できる形にする。

6. 全照合成功後だけ canonical receipt を返す。内部の予期しない通常例外も成功値へ変換せず、closed error に包む。

これらの閉包内 `file:line` はすべて**利用箇所の参照**であり、編集案ではない。

### `orchestrator/campaign/p3_b4_material_report.py`

- `:30` の import 群へ新 consumer と error 型を追加。
- `:265` の ledger error 処理後、`:267` の `evaluate_b4_artifacts` 呼出し直前へ consumer 呼出しを追加。
- 新 error を `:143` の `_fail` で包む。
- `:116` の `B4MaterialReportInputs`、report schema、JSON／Markdown 射影には field を増やさない。成功 receipt はこの呼出し内の検証結果として扱う。

### `orchestrator/tests/test_p3_b4_pair_completeness.py`

新設するテスト骨格は以下。

```text
test_complete_pair_binding_is_deterministic
test_pair_manifest_projection_mismatch
test_proposal_registry_mismatch
test_precursor_registry_mismatch
test_receipt_arm_slot_mismatch
test_existing_source_uniqueness_guard_is_reused
test_closed_input_schema
test_each_binding_check_has_an_independent_killer
```

純関数試験では、ledger 実 API で作った registry／manifest と合成 source を使用する。既存 `test_p3_b4_analysis_path.py` の source は単なる文字列であり、precursor も proposal と意図的に異なるため、**その既存正例を書き換えたり、新 consumer の正例として流用したりしない。**

実 issuer／producer が生む source schema・値域との適合は、次の production テストで別に確認する。

### `orchestrator/tests/test_p3_b4_material_report.py:266`

既存 `immutable_publication` fixture（`:147`）の実 API 出力を使い、既存正例に以下を追加する。

- 新 consumer が成功し、同じ bytes から同じ receipt を返す。
- 後述の 4 変異を assembly 戻り値に適用し、public builder が新理由で拒否する。
- evaluator を spy し、新 consumer 拒否後には呼ばれないことを確認する。
- 新 consumer を外した対照では同じ変異がその境界を通過することを確認する。
- 公開 API の拒否試験では report 3 ファイルが作られないことを確認する。

`:_load_and_evaluate` 自体を mock してはならない。それでは必須配線の証明にならない。

### `orchestrator/tests/acceptance_duration_ledger.json:2`

新 test file の全 nodeid を、実装段で得た JUnit 所要から登録する。既存の `tools/update_acceptance_duration_ledger.py:57` の CLI と `--coverage-against` を使い、収集された nodeid の欠落を確認する。

所要台帳の型・件数条件は `orchestrator/tests/conftest.py:1502` に従う。本 plan 段では所要値を作らない。

## 配線点

`p3_b4_material_report.py:265` と `:267` の間を次の形にする。

```python
try:
    pair_receipt = assert_b4_pair_complete(
        scheduled_registry_bytes=publication.registry.canonical_bytes,
        analysis_manifest_bytes=publication.manifest.canonical_bytes,
        raw_analysis_records_bytes=assembly.canonical_bytes,
        source_artifact_bytes=assembly.source_artifact_bytes,
    )
except B4PairCompletenessError as exc:
    _fail("pair_completeness_rejected", exc.reason.value, cause=exc)
```

成功後に既存 evaluator を呼ぶ。floor の有無、verdict、特定 campaign、CLI flag による検査回避を設けない。

証拠経路は既に以下で成立している。

- producer `:2255`：manifest 順に issuer 計画 path を読む。
- `:2275`：attempt artifact を証拠から再導出する。
- `:2289`：公開済み bytes との exact 一致を要求する。
- `:2344`：各 source の bytes を組み立てる。
- `:2387`：その bytes を assembly として返す。

新 consumer はこの読取結果を使う。二度目の filesystem 読取や新 writer は追加しない。

なお、`:244` の **assembly 自体が拒否された場合**は、従来どおり欠損を記述した材料 report を作り、分析しない。完全な pair が無いこの経路まで例外停止にすると既存正例を壊す。「無条件発火」は、**評価へ進む全 assembly に必須**という意味で実装する。毎回の report 生成に、欠損時も成功必須の検査を要求する読みは採らない。

閉包 5 module は import 先として利用するだけで、配線のための編集は不要である。

## 正例と負例

共通正例は、実 issuer／producer が公開した 201 pair・402 source の整合した assembly。解析結果の成功 verdict は要求しない。floor 未記入による既存 `floor_domain_error` は保持する。

以下の負例は**組立て後の消費境界の変異**である。計画 path の artifact を書き換えて producer の既存再導出を通過した、と主張しない。

| 性質 | 通る正例 | その性質だけを破る負例 |
|---|---|---|
| ① manifest ↔ pair 一対一 | 両 source の block／attempt が対応する manifest 行と一致 | 先頭 pair の両 source の `binding.block_id` だけを未登録 ID に変更。attempt、proposal、raw block、reference、assignment、arm は保持。変更 source の hash を raw receipt field に追随させる。 |
| ② proposal ↔ registry | 両 source の `binding.precursor_hash=P`、registry の同 attempt も `P` | 両 source の転記値だけを別の合法 hash `Q` に変更。raw precursor は `P` のまま。変更 source の hash を raw に追随させる。 |
| ③ raw precursor ↔ registry | raw on/off と registry がすべて `P` | raw on/off precursor だけを同じ `Q≠P` に変更。source bytes、source proposal、receipt は変えない。 |
| ④ receipt ↔ arm slot | raw on は `identity.arm=on`、off は `off` の source を参照 | 先頭 pair の source bytes の順序と raw の receipt hash を**同時に**交換する。raw arm 名、precursor、reference、assignment は保持する。 |

帰属の確認条件を固定する。

- 全負例で `_source_artifacts_match` が `True`。402 hash は一意で、raw 宣言と渡した source bytes の順序も一致する。
- raw の block 数・ID・reference・assignment は正例のまま。
- ②では③の比較先を registry の `P` とするため、③を同時に破らない。
- ③は on==off を保つため、既存 adapter `:562` と contract `:426` の比較を通る。
- ④は hash だけの交換ではない。hash だけを交換する既存 `test_source_artifact_digest_swap_between_arms_is_rejected` は、本機構の新規 killer に数えない。
- 合成正例では有効な `floor=0` を用い、凍結 evaluator が各負例を受理することも対照として要求する。

①の負例が破るのは**source から再生成した pair 行の manifest 対応**である。raw block 自体の欠落・重複は既存 adapter `:417`、`:538` などで既に拒否されるため、新機構の成果に数えない。

変異 matrix は次を要求する。

| 無効化する新照合 | 生存してしまう負例 |
|---|---|
| source pair の block／attempt と manifest の比較 | ① |
| source proposal と registry の比較 | ② |
| raw precursor と registry の比較 | ③ |
| source identity と raw arm slot の比較 | ④ |

いずれも、対象比較を外しても別検査で拒否されるなら独立 killer として失格とする。receipt の大域重複禁止は既存検査の回帰確認であり、この matrix の新規成果には含めない。

## 実装子への分割案

**実装子は 1 単位**とする。所有 path は変更面の表の 5 本すべて。

```text
orchestrator/campaign/p3_b4_pair_completeness.py
orchestrator/campaign/p3_b4_material_report.py
orchestrator/tests/test_p3_b4_pair_completeness.py
orchestrator/tests/test_p3_b4_material_report.py
orchestrator/tests/acceptance_duration_ledger.json
```

consumer、必須配線、production 正例、所要台帳を同じ変更単位で閉じる。閉包、producer、issuer、事前登録 doc の所有は渡さない。この plan 段では実装子を起動しない。

## 残る穴

- **同一 campaign 由来の証明はしない。** `initial_proposal_sha256` の権威 producer が無く、source proposal と raw precursor の一致は転記の一貫性である。
- 公開前の候補選別、別 publication root での再発行、協調した証拠一式の書換えは防がない。receipt shopping 全般が閉じたとは書かない。
- 新 consumer は既存 assembler が検証した source bytes を消費する。assembler 自体の悪意ある置換や、公開 artifact の不変性を保証するものではない。
- 凍結 `evaluate_b4_artifacts` の直接呼出しには新 consumer が入らない。既存 API とその合成正例は維持される。必須配線の保証範囲は material report の production 経路である。
- pair 完全性 receipt は材料レポート内部の検査結果であり、凍結 source closure に新 consumer の意味論が追加されたことを示さない。
- assembly 欠損時の材料 report は引き続き生成されるが、分析も pair 完全性の成功主張も行わない。
- 本段は静的確認のみ。実 API 正例、変異 matrix、既存 golden、所要台帳の実測、関連チェックの実行結果は実装段で必要になる。

## 総括

閉包外の consumer 1 本を、material report の評価直前に必須配線する。  
公開済み artifact の読取結果から pair 行を再生成し、manifest／registry と exact 照合する。  
receipt 重複禁止は既存実装を再利用し、新規成果に数えない。  
4 性質の負例は組立て後の消費境界で独立に作り、検査除去 matrix で帰属を確認する。  
閉じる主張は転記の一貫性と提出内の対の一意性までに限定する。  
編集・commit・docs 更新・pytest 実行は行っていない。