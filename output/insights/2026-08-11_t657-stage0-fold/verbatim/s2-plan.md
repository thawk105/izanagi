# 段 2 実装プラン

結論は P1〜P5 をすべて採用する。`required_gates` は 8→12 件、blocking gate は 3→4 件になるが、段 0 は引き続き `status=incomplete / pending_count=5 / unresolved_count=2` である。fixture 行・10 case・ruling profile は変更しない。

行番号は現行 base `856f4d4c` のもの。テストは指示どおり実行していない。

## 1. 編集面の完全な地図

### 親だけが編集する設計文書

対象: [calibration-freeze-authority-bundle-design.md:402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:402)

#### §7.5 namespace

現行 415–417 行:

```text
  approvals/                           # 上位承認 A
  active/                              # 上位 pointer X
```

置換後:

```text
  approvals/                           # 上位承認 A
  active/                              # 上位 pointer X
  revocations/                         # 上位失効 R
```

現行 419 行:

```text
file 名は原則としてその record 自身の raw sha256 (`<64hex>.json`)。候補 record だけ §6.1 の形。
```

置換後:

```text
file 名は原則としてその record 自身の raw sha256 (`<64hex>.json`)。候補 record だけ §6.1 の形、
失効 record だけ対象束の `bundle_digest` を stem とする。
```

#### §7.5 失効 record schema

[現行 449–464 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:449)では、X の exact 5 key の後に「namespace と schema は定めない」「固定 schema を land させてはならない」とある。

X の 449–452 行は維持し、453–464 行を次へ置換する。

```markdown
**失効 record R** — `revocations/<bundle_digest>.json`、束当たり 0/1 件、top-level exact 7 key。

| key | 型・制約 |
|---|---|
| `schema_version` | 逐語 `calibration-freeze-authority-revocation/v1` |
| `authority_bundle_generation` | exact int、1 以上 |
| `bundle_digest` | 64 lower-hex。file 名の stem、失効対象 X、X が参照する A の値と一致 |
| `revoked_active_pointer_raw_sha256` | 64 lower-hex。失効対象 X の raw bytes の sha256 と `active/<raw sha256>.json` の file 名 stem の双方に一致 |
| `revoked_by` | NFC、trim 済み、1〜128 code point |
| `revoked_at` | exact int の UTC 秒。`bool` は int として受理しない |
| `reason` | 非空 string |

同じ `bundle_digest` に対応する canonical path は 1 本だけなので、HEAD に置ける record は
構造的に 0/1 件である。同じ path に別 bytes の履歴がある場合や、field と X / A の参照が一致しない
場合は失効を無視せず解決不能として拒否する。raw bytes は §7.3 と同じ canonical JSON + 単一 LF とする。

- **上位 X が一度成立した後に上位権限が解決不能になった場合、下位 authority へ fallback しない。**
  失効を検出した場合も、record の重複・破損で一意に解決できない場合も、resolver は
  **terminal fail-closed** を返す。§1 の precedence 規則が下位を現行契約とするのは
  「上位 X が一度も成立していない HEAD」に限る。
- したがって失効は「解決不能」を**下位が肩代わりできない状態**として設計する。失効後に
  上位が承認していない環境と凍結の直積が再生成される経路はこれで閉じる。
```

太字の先頭行を検証器の literal marker とし、その直後に空行と `| key | 型・制約 |` が続く形を固定する。

#### §10 段 6 行

[現行 683 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:683):

```markdown
| 6 | 発効 X | **段 5 の後にしか置けない。** policy 未実装のまま X を置くと、X 自身が拒否されるか policy なしで production へ入るかの二択になる。判定式は段 0 と段 5 の裁定後に書く。**段 5 の除外は段 6 へ及ばない** — 段 6 は fixture 閉包の対象のままであり、その帰結は §12.3 のユーザー裁定待ちである |
```

置換後:

```markdown
| 6 | 発効 X | **段 5 の後にしか置けない。** **構造部分 (段 0 で固定):** (i) X は `active/<raw sha256>.json` に置く top-level exact 5 key (`schema_version` / `authority_bundle_generation` / `parent_active_pointer_raw_sha256` / `bundle_digest` / `approval_raw_sha256`) の record で、file 名の stem は X の raw sha256 と一致する。 (ii) `parent_active_pointer_raw_sha256` は genesis のときだけ `null`、それ以外は既存 X の raw sha256 と一致する。 (iii) `bundle_digest` は A の `bundle_digest` と一致する。 (iv) `approval_raw_sha256` は A の raw bytes の sha256 と `approvals/<raw sha256>.json` の file 名 stem の双方に一致する。 (v) 参照先 A は §5.1 の人間承認・topology 検査を通った承認済み A に限る。 以上 5 条件をすべて満たす陽性 control を少なくとも 1 件受理し、各条件を 1 件だけ破る 5 個の陰性変異をそれぞれ対応する理由で拒否する。 **policy 依存部分:** 段 5 の S / B 裁定後まで `CFAB-STAGE6-POLICY-PREDICATE` (owner = `user`, status = `unresolved`) として残し、段 6 の完了には構造部分と policy 依存部分の双方を要求する。段 5 の除外は段 6 へ及ばない |
```

#### §10.2 R2 の畳み込み

[現行 721–725 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:721)を次へ置換する。

```markdown
> **本節の第 1 条件は、先送り確定の `CFAB-S-SEAL` と `CFAB-B-SIDE-EFFECT` も数える。**
> 両者は applicable であり `unresolved` だから、**R2 = (b) により、S と B の裁定が land するまで
> 段 0 は `incomplete` のままである。** 段 5 の fixture 除外はこの条件に触れず、
> `_applicable_unresolved_count` を減らしたり applicability を広げたりして完了へ近づけてはならない。
```

#### §12.1 R1/R2/R3 の索引追加

[§12.1 表の末尾 801 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:801)の直後へ追加する。

```markdown
| R1 | **(a)** `revocations/<bundle_digest>.json`、exact 7 key、束当たり 0/1 件、UTC 秒 int | — (gate `CFAB-R1-REVOCATION-RECORD`) | §7.5 |
| R2 | **(b)** 段 0 完了は S / B の裁定後まで待つ | — (gate `CFAB-R2-STAGE0-COMPLETION`) | §10.2 |
| R3 | 段 6 を構造部分と policy 依存部分へ分割し、構造部分だけを段 0 で固定 | — (gate `CFAB-R3-STAGE6-PREDICATE`) | §10 の段 6 行 |
```

#### §12.3 の畳み込み

[現行 810–832 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:810)の R1/R2/R3 全文を置換する。

```markdown
### 12.3 残るユーザー裁定

**本 wave 時点で残るユーザー裁定はない。** 旧 R1 / R2 / R3 は §12.1 へ移し、
規則本文はそれぞれ §7.5 / §10.2 / §10 の段 6 行へ畳み込んだ。

§12.2 の S / B は先送り確定のままである。この「残る裁定なし」は S / B を解決済みと扱う意味ではなく、
`CFAB-S-SEAL` / `CFAB-B-SIDE-EFFECT` と `CFAB-STAGE6-POLICY-PREDICATE` は引き続き
段 0 完了を block する。
```

### U1: 契約検証器

対象: [calibration_freeze_authority_contract.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:47)

#### 定数・regex の追加

57 行の `_SELECTION_LITERAL_RE` 後へ次を追加する。

```python
_REVOCATION_TABLE_HEADING = (
    "**失効 record R** — `revocations/<bundle_digest>.json`、"
    "束当たり 0/1 件、top-level exact 7 key。"
)
_REVOCATION_TABLE_ROW_RE = re.compile(
    r"^\|\s*`([a-z][a-z0-9_]*)`\s*\|[^|]*\|\s*$"
)
_STAGE6_TABLE_ROW_RE = re.compile(
    r"^\|\s*6\s*\|\s*発効 X\s*\|\s*(.*?)\s*\|\s*$",
    re.MULTILINE,
)
_STAGE6_STRUCTURAL_MARKER = "**構造部分 (段 0 で固定):** "
_STAGE6_POLICY_MARKER = "**policy 依存部分:** "
_STAGE6_STRUCTURAL_CLAUSE_RE = re.compile(
    r"\((i|ii|iii|iv|v)\) (.+?。)"
    r"(?= \((?:i|ii|iii|iv|v)\)| 以上 5 条件)"
)
_STAGE6_POLICY_RE = re.compile(
    r"^段 5 の S / B 裁定後まで `(?P<gate_id>CFAB-[A-Z0-9-]+)` "
    r"\(owner = `(?P<owner>[a-z0-9-]+)`, "
    r"status = `(?P<status>[a-z-]+)`\) として残し、"
    r"段 6 の完了には構造部分と policy 依存部分の双方を要求する。"
    r"段 5 の除外は段 6 へ及ばない$"
)
```

[95 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:95)直後へ追加する定数は次の逐語とする。

```python
_REVOCATION_KEYS = frozenset({
    "schema_version",
    "authority_bundle_generation",
    "bundle_digest",
    "revoked_active_pointer_raw_sha256",
    "revoked_by",
    "revoked_at",
    "reason",
})
_EXPECTED_STAGE6_STRUCTURAL_PREDICATES = (
    "X は `active/<raw sha256>.json` に置く top-level exact 5 key "
    "(`schema_version` / `authority_bundle_generation` / "
    "`parent_active_pointer_raw_sha256` / `bundle_digest` / "
    "`approval_raw_sha256`) の record で、file 名の stem は X の raw sha256 と一致する。",
    "`parent_active_pointer_raw_sha256` は genesis のときだけ `null`、"
    "それ以外は既存 X の raw sha256 と一致する。",
    "`bundle_digest` は A の `bundle_digest` と一致する。",
    "`approval_raw_sha256` は A の raw bytes の sha256 と "
    "`approvals/<raw sha256>.json` の file 名 stem の双方に一致する。",
    "参照先 A は §5.1 の人間承認・topology 検査を通った承認済み A に限る。",
)
_EXPECTED_STAGE6_STRUCTURAL_CONTROL = (
    "以上 5 条件をすべて満たす陽性 control を少なくとも 1 件受理し、"
    "各条件を 1 件だけ破る 5 個の陰性変異をそれぞれ対応する理由で拒否する。"
)
```

#### §7.5 key 抽出関数

[既存 `_extract_design_selection_enums`:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:318)の直後へ `_extract_design_revocation_keys(path)` を追加する。

実装契約:

1. `### 7.5 上位層の namespace と record schema` が全文中に exact 1 回であることを要求する。
2. その見出しから直後の `\n---` までに限定する。
3. 同区間内で `_REVOCATION_TABLE_HEADING + "\n\n| key | 型・制約 |\n|---|---|\n"` が exact 1 回であることを要求する。
4. その直後から最初の空行までだけを table body とし、全行を `_REVOCATION_TABLE_ROW_RE.fullmatch()` する。
5. key 重複を拒否し、`frozenset[str]` を返す。

これにより、同じ §7.5 内にある承認 A の 7 key 表は、

- exact marker が異なる
- 失効 marker より前にある
- table body の切り出し範囲外

の三重条件で取得不能になる。

[既存 `_validate_ruling_profile`:523–535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:523)では selection enum 検査の直後へ追加する。

```python
design_revocation_keys = _extract_design_revocation_keys(design_doc)
if design_revocation_keys != _REVOCATION_KEYS:
    raise ContractError(
        "design §7.5 revocation record keys do not exactly match validator keys"
    )
```

これは `_extract_design_selection_enums` → `_validate_ruling_profile` の既存経路と同型である。

#### 段 6 構造 predicate 抽出関数

同じ抽出関数群へ `_extract_stage6_contract(path)` を追加する。返却値は次とする。

```python
tuple[
    tuple[str, ...],       # (i)〜(v) の本文
    str,                   # 陽性 + 5 陰性 control 文
    tuple[str, str, str],  # policy gate_id / owner / status
]
```

処理は以下を exact に行う。

- `## 10. 段階分割と完了判定` から次の `## ` までに限定。
- `_STAGE6_TABLE_ROW_RE` が exact 1 行を得ることを要求。
- 先頭の `**段 5 の後にしか置けない。** `、構造 marker、policy markerを exact に要求。
- `(i)`〜`(v)` が固定順・重複なしであることを要求。
- clause 外の残余が `_EXPECTED_STAGE6_STRUCTURAL_CONTROL` だけであることを要求。
- policy 部分を `_STAGE6_POLICY_RE.fullmatch()` し、gate tuple を返す。

[既存 `_validate_repository`:748–762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:748)へ、fixture assignment gate 照合の直前に追加する。

```python
stage6_predicates, stage6_control, stage6_policy_gate = (
    _extract_stage6_contract(design_doc)
)
if (
    stage6_predicates != _EXPECTED_STAGE6_STRUCTURAL_PREDICATES
    or stage6_control != _EXPECTED_STAGE6_STRUCTURAL_CONTROL
):
    raise ContractError("design §10 stage 6 structural predicates drifted")

stage6_policy_gates = [
    (entry["gate_id"], entry["owner"], entry["status"])
    for entry in manifest["required_gates"]["entries"]
    if entry["gate_id"].startswith("CFAB-STAGE6-POLICY-")
]
if stage6_policy_gates != [stage6_policy_gate]:
    raise ContractError(
        "design §10 stage 6 policy gate does not exactly match required_gates"
    )
```

#### required gate pin

[現行 138–154 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:138)を次へ置換する。

```python
_EXPECTED_REQUIRED_GATES = frozenset({
    ("CFAB-Q3-REVOCATION", "user", "resolved"),
    ("CFAB-Q3-ROLLBACK", "user", "resolved"),
    ("CFAB-Q3-XF-POSITION", "user", "resolved"),
    ("CFAB-R1-REVOCATION-RECORD", "user", "resolved"),
    ("CFAB-R2-STAGE0-COMPLETION", "user", "resolved"),
    ("CFAB-R3-STAGE6-PREDICATE", "user", "resolved"),
    ("CFAB-S8-S10-CONTRADICTION", "user", "resolved"),
    ("CFAB-STAGE6-POLICY-PREDICATE", "user", "unresolved"),
    (
        "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT",
        "stage1-and-later",
        "pending",
    ),
    ("FREEZE-AX-TOPOLOGY", "lower-impl-wave", "nonconforming"),
    ("FREEZE-CONFORMANCE-LITERAL", "lower-wa-wave", "unresolved"),
    ("FREEZE-U-A1", "user", "resolved"),
})
_EXPECTED_REQUIRED_GATES_ENTRIES_SHA256 = (
    "26aa463b024e9f64e87401ca3dcebd508efe146ed28c166557a6a4447811b948"
)
```

[_validate_manifest の gate 部 460–506 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:460)は置換しない。既に以下をすべて担う。

- `count == len(entries)`
- `gate_id` 重複拒否
- `(gate_id, owner, status)` と `_EXPECTED_REQUIRED_GATES` の exact 集合一致
- canonical entries hash、manifest literal、module pin の三者一致

brief §7 の「3 つの sha256 pin」は、正確には「保存 literal 2 個 + 実行時再計算値 1 個」の三者照合である。更新する保存 literal は module と manifest の2か所だけ。

### U1: manifest

対象: [manifest.v1.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/fixtures/calibration_freeze_authority/manifest.v1.json:1)

現行 `required_gates` 値:

```json
{"count":8,"entries":[{"gate_id":"CFAB-Q3-REVOCATION","owner":"user","status":"resolved"},{"gate_id":"CFAB-Q3-ROLLBACK","owner":"user","status":"resolved"},{"gate_id":"CFAB-Q3-XF-POSITION","owner":"user","status":"resolved"},{"gate_id":"CFAB-S8-S10-CONTRADICTION","owner":"user","status":"resolved"},{"gate_id":"CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT","owner":"stage1-and-later","status":"pending"},{"gate_id":"FREEZE-AX-TOPOLOGY","owner":"lower-impl-wave","status":"nonconforming"},{"gate_id":"FREEZE-CONFORMANCE-LITERAL","owner":"lower-wa-wave","status":"unresolved"},{"gate_id":"FREEZE-U-A1","owner":"user","status":"resolved"}],"entries_sha256":"93cfe2b396d4831800537967d67628c7bca38b8b7595c4ffedaccb5e88211e41"}
```

置換後:

```json
{"count":12,"entries":[{"gate_id":"CFAB-Q3-REVOCATION","owner":"user","status":"resolved"},{"gate_id":"CFAB-Q3-ROLLBACK","owner":"user","status":"resolved"},{"gate_id":"CFAB-Q3-XF-POSITION","owner":"user","status":"resolved"},{"gate_id":"CFAB-R1-REVOCATION-RECORD","owner":"user","status":"resolved"},{"gate_id":"CFAB-R2-STAGE0-COMPLETION","owner":"user","status":"resolved"},{"gate_id":"CFAB-R3-STAGE6-PREDICATE","owner":"user","status":"resolved"},{"gate_id":"CFAB-S8-S10-CONTRADICTION","owner":"user","status":"resolved"},{"gate_id":"CFAB-STAGE6-POLICY-PREDICATE","owner":"user","status":"unresolved"},{"gate_id":"CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT","owner":"stage1-and-later","status":"pending"},{"gate_id":"FREEZE-AX-TOPOLOGY","owner":"lower-impl-wave","status":"nonconforming"},{"gate_id":"FREEZE-CONFORMANCE-LITERAL","owner":"lower-wa-wave","status":"unresolved"},{"gate_id":"FREEZE-U-A1","owner":"user","status":"resolved"}],"entries_sha256":"26aa463b024e9f64e87401ca3dcebd508efe146ed28c166557a6a4447811b948"}
```

配列順は `gate_id` 昇順。JSON canonicalization は object key を sort するが配列順を sort しないため、この順序自体が hash の一部である。

hash は [_canonical_bytes:157–167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:157)と [_sha256_canonical:170–171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:170)を read-only で呼んで算出した値であり、LF は原像に含まれない。親は U1 prompt に上記値を渡し、U1 は更新後の `entries` に同 helper を再適用して照合する。literal の手計算は禁止する。

### U2: 契約テスト

対象: [test_calibration_freeze_authority_contract.py:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:135)

既存変更:

- 178–181 行: `blocking_gates=3` → `blocking_gates=4`。
- 211–224 行: gate snapshot を上記 12 件の同順序へ置換。
- 544 行: removal 負例の対象を `CFAB-Q3-REVOCATION` から `CFAB-R1-REVOCATION-RECORD` へ置換。
- 227–235 行の independent hash test は本体変更不要。新 module pin を自動参照する。

新規 nodeid は7件。

## 2. Drift 束縛の性質

### §7.5 key 表

束縛するのは裁定どおり「key 集合」であり、型・長さ・NFC 等の各 cell 全文ではない。

```text
§7.5 exact heading
  → 失効 record の exact literal marker
    → 直後の exact table header
      → 最初の空行までの key rows
        → frozenset == _REVOCATION_KEYS
```

承認 A の表も7件だが、失効 marker より前にあり、marker も異なるため誤取得しない。canonical 正例で期待する7 keyを直接 assertするテストも置くため、誤って A を取る extractor は reject-all 以前に陽性で赤になる。

### 段 6 構造 predicate

単なる `CFAB-STAGE6-*` ID の存在検査にはしない。IDだけ残して prose を緩める実装が通るためである。

- (i)〜(v) の全文を独立定数と exact 比較
- roman label の順序・件数も固定
- 陽性1件以上 + 単一変異5件という control 文も exact 比較
- policy gate の ID・owner・status は設計行から抽出し manifest と一致
- manifest の独立 `_EXPECTED_REQUIRED_GATES` pinも維持

この wave が保証するのは設計 predicate の機械束縛までであり、X resolver の実実行を保証したとは扱わない。実行 fixture は既存 assignment gate が `pending` のため、段 0 は閉じない。

## 3. 陽性・陰性テスト

追加する完全な一覧:

| nodeid | 種別 | 固定するもの／殺す変異 |
|---|---|---|
| `test_design_revocation_record_keys_match_validator_schema` | 陽性 | canonical §7.5 から P2 の7 keyだけを抽出し、`_REVOCATION_KEYS` と一致。A の7 key表を誤取得する extractor と reject-all を殺す |
| `test_design_revocation_record_key_substitution_is_rejected` | 陰性 | `revoked_active_pointer_raw_sha256` を `approval_raw_sha256` に置換して件数7を維持。件数だけ見る validator を殺す |
| `test_design_stage6_structural_predicates_match_validator_contract` | 陽性 | canonical (i)〜(v)、陽性/陰性 control 文、policy gate tuple の exact 値を確認。reject-all を殺す |
| `test_design_stage6_structural_predicate_relaxation_is_rejected` | 陰性 | (v) の「人間承認・topology 検査を通った承認済み A」を「schema が一致する A」へ docs だけ緩和。predicate 全文 pin が落とす |
| `test_design_stage6_policy_gate_id_drift_is_rejected` | 陰性 | docs の gate IDだけを `CFAB-STAGE6-POLICY-PREDICATE-RELAXED` へ変更。manifestとの導出一致が落とす |
| `test_stage6_policy_gate_cannot_be_resolved_early` | 陰性 | manifest の policy gateを `unresolved`→`resolved`、entries hashも追随更新。independent gate set pinが落とす |
| `test_stage0_remains_incomplete_after_r1_r2_r3_projection` | 陽性 | canonical repositoryが整合検証を通り、`incomplete / pending=5 / unresolved=2`、blocking gate exact 4件であることを固定 |

既存 nodeid の役割:

- `test_current_repository_is_rejected_as_stage0_incomplete`: `require_stage0_complete()` の exact 診断を `blocking_gates=4` で固定。
- `test_adjudicated_ruling_and_gate_projection_is_exact`: R1/R2/R3 resolved と policy unresolved を含む12件を固定。
- `test_required_gate_removed_is_rejected`: R1 gate削除を、count/hash追随後も拒否。
- `test_required_gate_reorder_with_refreshed_manifest_hash_is_rejected`: 新しい12件配列でも順序 pin を維持。
- `test_required_gate_entries_have_independent_module_sha_pin`: canonical bytes・manifest・moduleの三者一致を維持。
- `test_real_repository_contract_is_consistent_but_incomplete`: canonical入力の受理を維持する既存陽性。

## 4. Provisional 裁定の評価

- P1 — 採用。R1/R2/R3は束ごとに選択値が変わる項目ではなく、globalな設計完了判断である。profileへ入れると `_PROFILE_IDS`、profile bytes、applicabilityを不要に動かす。resolved gateとして投影するのが既存 `CFAB-S8-S10-CONTRADICTION` と同型。
- P2 — 採用。7 keyは schema/generation/bundle/X/actor/time/reason を過不足なく持ち、対象を「承認 A」ではなく「発効 X」に束縛する。
- P3 — 採用。policy依存部分を profileへ偽装せず、owner=user・unresolvedのblocking gateとして残す。statusは既に incomplete なので完了可否を緩めない。
- P4 — 採用。5述語の論理積と陽性/陰性条件を全文束縛する。IDだけの自己申告にはしない。
- P5 — 採用。これはschema・語彙・設計predicateの確定waveであり、段6実行fixtureを新設したふりにしない。

P2の代替7 key案は次である。

```text
schema_version
authority_bundle_generation
bundle_digest
approval_raw_sha256
revoked_by
revoked_at
reason
```

これは `revoked_active_pointer_raw_sha256` を `approval_raw_sha256` に置き換える案である。却下する。A は `approved-inactive` でも存在でき、approval hashだけでは、どのXがそのAを発効させ、どのparent chain上にあったかを固定しない。P2はXのraw hashを通じて generation・bundle digest・approval参照・parent ancestryをまとめて束縛するため、非発効Aを対象にした失効を受理しない。したがってP2の方が受理集合として狭く、強い。

## 5. 段 5 の所有分割

brief §7 の U1→U2 逐次で正しい。fixture JSONを第3単位へ分けない。

実際の順序は次とする。

1. 親が docs の上記変更を適用。
2. U1が `contract.py` と `manifest.v1.json` を同時所有し、gate配列・独立pin・extractorを一貫して更新。
3. U2がU1の private定数・helper・診断文字列を読み、テストを追加・更新。
4. 親が関連テストと全走を実測。

manifestを第3単位にすると、module pinとmanifest literalが別所有になり、途中状態では必ず三者照合が破れる。独立性の利益がなく、hashの受け渡し面だけ増える。

親の docs 編集は実装子単位に数えない。U1/U2はいずれも `docs/**` を編集しない。

## 6. 波及の静的列挙

### `load_manifest`

- [calibration_freeze_authority_execution.py:711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_execution.py:711) — fixture IDだけを読む。gate件数非依存で破損なし。
- [test_calibration_freeze_authority_execution.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_execution.py:49) — fixture ID集合だけを読む。破損なし。
- [test_calibration_freeze_authority_contract.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:207) — gate tuple snapshot。8→12で更新必須。
- [test_calibration_freeze_authority_contract.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:230) — hash三者一致。module/manifest pin更新後は本体変更不要。

### `load_ruling_profile`

- [test_calibration_freeze_authority_contract.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:189)のみ。profile 12件は不変なのでsnapshot変更なし。新しい§7.5 drift検査が同load pathに加わる。

### `validate_repository`

- [test helper:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:128) — 全 synthetic負例の共通入口。canonical設計を複製するため既存負例は維持。
- [canonical positive:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:138) — 要約値は不変。
- [require_stage0_complete 内部:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:894) — blocking gate数だけ3→4。

### `require_stage0_complete`

- [test_calibration_freeze_authority_contract.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:176)のみ。exact診断の `blocking_gates=3` が `4` へ変わるため更新必須。

repo全体にこれ以外の実callerはない。`tools/codex_worker_ledger.py` の `_load_manifest` は別のprivate関数、`s8c_preregistration_evidence_contract.v1.json` や `output/insights/**` の文字列は同名言及でありcallerではない。

直接壊れるconsumerは、gate snapshot、manifest/module hash pin、`require_stage0_complete` のblocking件数期待値の3系統だけである。production consumerは存在しない。

### 明示的 no-touch

- `ruling-profile.v1.json`
- `cases/*.json` 全10件
- `calibration_freeze_authority_execution.py`
- `test_calibration_freeze_authority_execution.py`
- `_PROFILE_IDS` / `_SELECTION_ENUMS` / `_EXPECTED_RULING_STATES`
- `_EXPECTED_RAW_SHA256_BY_FIXTURE`
- `_EXPECTED_FIXTURE_ENTRIES_SHA256`
- `_EXPECTED_ROW_IDS_SHA256`
- manifest の `fixtures` / `row_coverage`
- `_applicable_unresolved_count`

## 総括

- 採用した provisional 裁定: P1, P2, P3, P4, P5／却下した provisional 裁定: なし
- 実装子 U1: `calibration_freeze_authority_contract.py`, `manifest.v1.json`・新規 0 nodeid／U2: `test_calibration_freeze_authority_contract.py`・新規 7 nodeid（既存 3 nodeid 更新）
- プランが依存する未確認事実: なし（テスト実測は本依頼どおり親へ委譲し、本段では未実行）