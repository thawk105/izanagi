# T-793 実装プラン

結論は **NO-GO（現 brief のまま 4 要件を一括で land する場合）** とする。(iii) の source-side 本走 gate は、pubcore v2 §10.2 と緊張関係にあり、既存 decision だけでは接続権限が一意に定まらないためである。

ただし、(i)・(ii)・(iv)・(iv-b) は実装可能であり、(iii) も新しい canonical decision が fold されれば同じ設計のまま実装できる。以下はその分割可能な実装計画である。指定どおり、ファイル変更・commit・テスト実行は行っていない。

## 1. 実装境界

本 wave では次を作る。

1. 固定パスの publication reservation 台帳と、append-only/create-only 検証。
2. 承認対象 blob の未確定 marker を、承認/fold の共通経路で拒否する gate。
3. source main 実行前の reservation 前提検査。ただし新 D の fold まで接続・land しない。
4. `F_p` の D291 payload を唯一の trust root とする parser/resolver/report。
5. Addendum P の `p01`〜`p03` exact-key 検査。

作らないものは以下である。

- pilot/main submission を許可する API
- submission 禁止を解除する状態遷移
- primary reservation 台帳の変更
- D291 が承認した文書 bytes の変更
- `authority: none` の書き換え
- publication reservation の取消・更新・解放 API
- `FROZEN_MANIFEST` の変更

## 2. 新規・変更ファイル

### 2.1 新規ファイル

| file:line | 責務 |
|---|---|
| `orchestrator/publication/__init__.py:new:L1-L45` | 安定した公開 API のみを再 export。「allowed」「ready」「admitted」を含む名前は export しない。 |
| `orchestrator/publication/ledger.py:new:L1-L450` | 固定 publication 台帳の schema、履歴検証、primary との互いに素性、原子的な一件追加。 |
| `orchestrator/publication/approval_d291.py:new:L1-L520` | `F_p` の `docs/decisions.md` から D291 fenced payload を厳密に parse し、role・relation・approved values を解決する。 |
| `orchestrator/publication/addendum_p_envelope.py:new:L1-L55` | Addendum P の fields がちょうど `p01,p02,p03` であることを検査する固定 wrapper。 |
| `orchestrator/publication/approval_guard.py:new:L1-L240` | approval fragment から承認対象 blob ref を抽出し、固定 blob を読んで未確定 marker を拒否する。 |
| `orchestrator/publication/admission.py:new:L1-L130` | source main の「reservation 前提だけ」を検査する deny-only predicate。新 D が fold されるまで land 対象外。 |
| `orchestrator/publication/report.py:new:L1-L190` | D291 role 解決結果を副作用なしで構造化し、決定的 JSON として表示する。 |
| `output/registry/t139-publication-reservations.jsonl:new:0 bytes` | publication 系列唯一の台帳。予約 entry はまだ発行せず、空の tracked file として導入する。 |
| `orchestrator/tests/test_t793_publication_ledger.py:new:L1-L460` | 台帳 schema、履歴、一意性、非解放、primary との互いに素性。 |
| `orchestrator/tests/test_t793_publication_approval.py:new:L1-L540` | D291 grammar、trust-root、role resolver、relation 全体一致、report。 |
| `orchestrator/tests/test_t793_publication_gates.py:new:L1-L300` | Addendum P exact-key、marker gate、source precondition。 |

### 2.2 変更ファイル

| file:line | 変更 |
|---|---|
| `tools/spool_fold.py:L936-L1038` | `_discover()` が decision fragment を確定した後、承認対象 blob を `approval_guard` で検査する。これにより `validate_spool_tree()` と `plan_fold()` の双方が同じ gate を通る。fold の適用処理自体は変更しない。 |
| `orchestrator/tests/test_spool_fold.py:既存の decision-fragment fixture/test 群付近` | marker のない承認対象が通る正例と、marker を含む固定 blob が `plan_fold()` で落ちる負例を追加する。fixture には新しい guard module を含める。 |
| `orchestrator/tests/test_check_docs.py:既存 spool guard test 群付近` | `check_docs` が `validate_spool_tree()` 経由で同じ marker 違反を報告する統合テストを追加する。 |

`tools/check_docs.py` 自体は変更しない。既存の `_check_spool_guard()`（現在の L797-L848）と `main()` からの呼び出し（現在の L4648）が `validate_spool_tree()` を利用しているため、`spool_fold.py` 側への結線で十分である。

### 2.3 変更しないファイル

- `orchestrator/preregistration/addendum_envelope.py`
- `orchestrator/preregistration/blobref.py`
- `orchestrator/preregistration/erratum.py`
- `orchestrator/tests/test_t139_preregistration_binding.py`
- `output/registry/t139-alpha-reservations.jsonl`
- `orchestrator/tests/test_frozen_artifacts.py`
- D291 が承認した二文書

## 3. 公開 API

### 3.1 `ledger.py`

```python
PUBLICATION_LEDGER_RELATIVE_PATH: Final[str]
PUBLICATION_FAMILY_ROOT: Final[str]
PUBLICATION_KIND: Final[Literal["individual_publication"]]
PUBLICATION_SCHEMA_VERSION: Final[Literal["t139-publication-reservation/v1"]]

@dataclass(frozen=True, slots=True)
class PublicationReservation:
    schema_version: Literal["t139-publication-reservation/v1"]
    family_root: str
    kind: Literal["individual_publication"]
    ordinal: int

@dataclass(frozen=True, slots=True)
class PublicationLedgerSnapshot:
    path: Path
    entries: tuple[PublicationReservation, ...]
    sha256: str
    inspected_head: str
    history_commits: tuple[str, ...]

def publication_ledger_path(
    repository_root: str | os.PathLike[str],
) -> Path: ...

def parse_publication_ledger(
    blob: bytes,
) -> tuple[PublicationReservation, ...]: ...

def inspect_publication_ledger(
    repository_root: str | os.PathLike[str],
) -> PublicationLedgerSnapshot: ...

def reserve_next_publication(
    repository_root: str | os.PathLike[str],
) -> PublicationReservation: ...
```

`reserve_next_publication()` は path・root・kind・ordinal を引数に取らない。今回承認されている ordinal は `1` のみなので、空台帳に exact な一行を追加する以外は拒否する。

検証事項は以下である。

- UTF-8 JSONL、終端 LF、空行なし
- JSON duplicate key 拒否
- exact key set:
  `schema_version,family_root,kind,ordinal`
- `bool` を整数として受理しない
- canonical JSON encoding
- `(family_root, kind, ordinal)` の重複拒否
- ordinal の単調性と許可済み範囲
- symlink・非 regular file 拒否
- Git 履歴が byte-prefix append-only
- 導入後の削除、truncate、書換え、delete/recreate を拒否
- primary 台帳との tuple-space 互いに素性
- append 時は lock、inode 再確認、`fsync(fd)` と親 directory の `fsync`

pubcore §8.1 の「primary と同じ commit」という記述は実台帳と矛盾するため、不変条件にしない。publication root/kind は D291 が承認した `88d68f91…` / `individual_publication`、primary は実台帳の `dce4ae4f…` / `alpha_reservation` として個別に固定する。

### 3.2 `approval_d291.py`

```python
D291_FOLD_COMMIT: Final[str] = (
    "b13b7ea840ad51199f40b3a534c9d1cdb422af2e"
)
D291_DECISIONS_SHA256: Final[str] = (
    "3d2cd5dc6cf63c5928a3ec64a91ae3b3c530dafc83d83d52a038a2eb5cf0c2b8"
)

ApprovedRoleName = Literal["publication_core", "source_addendum_b"]

@dataclass(frozen=True, slots=True)
class D291ApprovalPayload:
    decision_kind: str
    source_core: BlobRef
    source_addendum_a: BlobRef
    document_relations: DocumentRelations
    approved_roles: tuple[ApprovedRole, ...]
    approved_values: ApprovedValues
    operational_state: OperationalState
    operational_boundary: str

@dataclass(frozen=True, slots=True)
class D291RoleResolution:
    role_name: ApprovedRoleName
    semantic_role: str
    ref: BlobRef
    approval_status: Literal["approved_by_canonical_decision"]
    trust_root_commit: str
    submission_authority: Literal["not_granted"]

def parse_d291_payload(
    decisions_blob: bytes,
    *,
    fold_commit: str = D291_FOLD_COMMIT,
) -> D291ApprovalPayload: ...

def load_d291_payload(
    repository_root: str | os.PathLike[str],
) -> D291ApprovalPayload: ...

def require_d291_projection_exact(
    payload: D291ApprovalPayload,
    projection: Mapping[str, object],
) -> None: ...

def resolve_d291_role(
    repository_root: str | os.PathLike[str],
    *,
    role: ApprovedRoleName,
    candidate: BlobRef,
) -> D291RoleResolution: ...
```

`load_d291_payload()` は次を行う。

1. `F_p:docs/decisions.md` を直接読む。
2. blob SHA-256 が固定値と一致することを確認する。
3. `## D291` から `## D292` 直前までを切り出す。
4. fenced block がちょうど一つであることを確認する。
5. 全 payload を exact grammar で parse する。
6. `candidate` は payload から得た role triple と完全一致させる。
7. `BlobRef` で blob bytes を再検証する。

manifest や report に書かれた「承認済み」状態を trust root にしない。

### 3.3 `addendum_p_envelope.py`

```python
PUBLICATION_EXACT_FIELDS: Final[frozenset[str]] = frozenset(
    {"p01", "p02", "p03"}
)

def require_approved_addendum_p_fields(blob: bytes) -> None: ...
```

既存の `parse_addendum_fields()` を流用するが、期待集合を caller 引数にしない。これにより `p04` の追加、欠落、重複を受理集合の変更で回避できない。

### 3.4 `approval_guard.py`

```python
UNRESOLVED_APPROVAL_MARKERS: Final[tuple[bytes, bytes]]

@dataclass(frozen=True, slots=True)
class ApprovalTarget:
    role: str
    ref: BlobRef

def require_no_unresolved_approval_markers(blob: bytes) -> None: ...

def validate_approval_fragment_targets(
    repository_root: str | os.PathLike[str],
    *,
    fragment_path: str,
    fragment_body: bytes,
) -> tuple[ApprovalTarget, ...]: ...
```

fragment 自身を文字列検索するだけではなく、`approved_blobs:` の各 exact triple を読み、固定先 blob の bytes を検査する。P draft にある説明用 marker を無差別に検索しない。

### 3.5 `admission.py`

新 D の fold 後にのみ導入する。

```python
@dataclass(frozen=True, slots=True)
class ReservationPreconditionWitness:
    reservation: PublicationReservation
    ledger_sha256: str
    inspected_head: str
    submission_authority: Literal["not_granted"]

def require_source_main_publication_reservation_precondition(
    repository_root: str | os.PathLike[str],
) -> ReservationPreconditionWitness: ...
```

親案の `require_publication_reservation_for_main_run()` は、成功が main 実行の授権に見えるため採用しない。戻り値も boolean ではなく、検査した事実と `submission_authority="not_granted"` を持つ witness とする。

### 3.6 `report.py`

```python
@dataclass(frozen=True, slots=True)
class ApprovalReport:
    trust_root_commit: str
    decision_kind: str
    roles: tuple[D291RoleResolution, ...]
    operational_state: OperationalState
    submission_authority: Literal["not_granted"]

def build_approval_report(
    repository_root: str | os.PathLike[str],
) -> ApprovalReport: ...

def approval_report_to_dict(
    report: ApprovalReport,
) -> dict[str, object]: ...

def main(argv: Sequence[str] | None = None) -> int: ...
```

report は stdout への決定的 JSON のみとし、ファイルを生成しない。`future_publication_addendum_p` は relation として表示しても、approved role には含めない。

## 4. D291 payload の exact grammar

### 4.1 top-level exact-key 集合

fenced payload の top-level key は、次の 14 個だけを、この順序で許す。

1. `decision_kind`
2. `prior_exact_byte_authority`
3. `procedural_history`
4. `source_core`
5. `source_study_inputs`
6. `document_relations`
7. `approved_blobs`
8. `approved_values_for_future_addendum_p`
9. `historical_candidates_rejected_for_role`
10. `exact_closure`
11. `operational_state_on_fold`
12. `authority_field_note`
13. `role_coupling`
14. `operational_boundary`

欠落、重複、追加、順序変更を拒否する。

### 4.2 key ごとの形

| key | 文法・nested exact keys |
|---|---|
| `decision_kind` | 単一 `key = scalar` |
| `prior_exact_byte_authority` | `key = none` と、その構造化された継続説明行 |
| `procedural_history` | prose block。行順と本文を保持 |
| `source_core` | `{path, commit, sha256}` |
| `source_study_inputs` | prose と bare block `addendum_a`。`addendum_a` は `{path, commit, sha256}` |
| `document_relations` | 下記三 role の全 subtree |
| `approved_blobs` | bare block `publication_core` と `source_addendum_b`。各 `{path, commit, sha256}` |
| `approved_values_for_future_addendum_p` | `{approval_scope,p01,p02,p03_approved,addendum_p_blob_approved,value_projection}` |
| `historical_candidates_rejected_for_role` | `publication_core role` と `source_addendum_b role`。各 `{path,commit,sha256,note}` |
| `exact_closure` | numbered clause 1〜6。行順・本文を保持 |
| `operational_state_on_fold` | `{addendum_p_blob,p03,pilot_submission,main_submission,deny_basis,addendum_p_freeze_precondition,source_main_run_gate}` |
| `authority_field_note` | prose block |
| `role_coupling` | prose/list block |
| `operational_boundary` | `key = """` で始まり、独立した `"""` で閉じる三重引用 block |

`p01` は `{candidate_cap,admissible_ordinals}`、`p02` は次の exact keys とする。

- `familywise_alpha`
- `spending_domain`
- `alpha_pub_k`
- `current_k`
- `alpha_pub`
- `unspent_tail_reclaim`
- `unspent_tail_redistribute`

### 4.3 `document_relations` 全体一致

top-level role 集合は次の三つだけとする。

- `source_addendum_b`
- `publication_core`
- `future_publication_addendum_p`

nested exact keys は次のとおり。

```text
source_addendum_b:
  role
  satisfies
  depends_on
  independent_of

publication_core:
  role
  study_label
  pins_source_study_one_way
  note

future_publication_addendum_p:
  role
  satisfies
  depends_on
  blob_approved
  required_core_ref:
    path
    commit
    sha256
```

実装上は選択的な field 比較を行わない。次の手順で節全体を比較する。

1. indentation を構文として再帰的 node tree にする。
2. 各階層で exact-key 集合を照合してから正規化する。
3. scalar は構文上の `=` 周辺だけを正規化し、本文は保持する。
4. continuation 行は構造 indent だけを外し、本文・順序・改行を保持する。
5. `[ ... ]` は用途別に型付けする。
   - relation の list は順序付き token list。
   - `admissible_ordinals` は整数集合として比較する。
6. `required_core_ref.commit = symbolic:F_p` だけを固定 `F_p` に置換する。任意の symbolic ref は認めない。
7. 正規化後の subtree 全体を canonical nested tuple にし、期待 subtree と exact 比較する。

したがって、`note` の削除、未知 nested key の追加、role 値の変更もすべて失敗する。

### 4.4 `<->` mapping

`value_projection` では次の 9 行だけを許す。

```text
p01.candidate_cap <-> p01.candidate_cap
p01.admissible_ordinals <-> p01.admissible_ordinals
p02.familywise_alpha <-> p02.familywise_alpha
p02.spending_domain <-> p02.spending.domain
p02.alpha_pub_k <-> p02.spending.alpha_pub_k
p02.current_k <-> p02.current_study.k
p02.alpha_pub <-> p02.current_study.alpha_pub
p02.unspent_tail_reclaim <-> p02.unspent_tail.reclaim
p02.unspent_tail_redistribute <-> p02.unspent_tail.redistribute
```

左右 token と行数を exact 比較する。10 行目の追加、左右入替え、未知 path を拒否する。

比較単位は D291 に従う。

- 数値: `Decimal`
- ordinal: integer set、順序非依存
- boolean: boolean
- `spending_domain` / `alpha_pub_k`: strip と連続空白の collapse 後に canonical string と比較
- その他の文字列: exact

`p01.immutable...` と `p02.affects_primary_alpha` を approved value に読み替えない。一方で Addendum P envelope 全体は `p01`〜`p03` の exact-key gate に通す。

### 4.5 三重引用

`operational_boundary` だけに `"""` を許す。

- opening は `operational_boundary = """` の exact form
- closing は同じ indentation level の独立した `"""`
- 内部改行と本文は保持
- 二つ目の三重引用 field、末尾 text、未終端を拒否

汎用 YAML parser は使用しない。D291 固有 grammar として未知構文を fail-closed にする。

## 5. 台帳と予約 entry

### 5.1 entry は発行しない

この wave では reservation entry を発行しない。D292 により main/pilot は禁止されたままであり、「実装したため ordinal 1 を予約する」という推論はできない。

### 5.2 空ファイルを採用する理由

不存在を「空台帳」と扱う設計は採用しない。空の tracked file を作る。

挙動の差は以下である。

| 状態 | 空 tracked file | file 不存在を空扱い |
|---|---|---|
| 唯一の canonical path | 導入 commit から固定できる | 初回作成時まで確定しない |
| 後日の削除 | 履歴違反として拒否できる | 空状態へ戻ったと誤認し得る |
| delete/recreate | Git 履歴で拒否できる | 初回作成と区別しにくい |
| admission | `entries == ()` として明示的に拒否 | 「未導入」と「未予約」が混同される |
| fail-closed 性 | 高い | 低い |

空ファイルは「台帳は存在するが reservation はない」という状態を一意に表す。

### 5.3 `FROZEN_MANIFEST`

23 件の `FROZEN_MANIFEST` は変更しない。publication 台帳は将来 append される可変 artifact なので、whole-file digest を frozen manifest に入れると正当な追記まで失敗する。代わりに Git の prefix history、canonical JSONL、lock、inode 検査で append-only 性を守る。

## 6. marker gate

marker は承認文書の固定 blob bytes に対して検査する。

```text
decision fragment
  → approved_blobs の exact triple
  → read_pinned_blob()
  → unresolved marker scan
  → validate_spool_tree / plan_fold
```

`check_docs` だけに gate を追加する案は採用しない。直接 `plan_fold()` を呼ぶ経路が迂回可能になるからである。`_discover()` に置けば、validation と実 fold plan が同じ検査を共有する。

拒否対象は P draft 36・37 行目の二つの exact marker とする。一般的な「未確定」語や説明文までは拒否しない。

## 7. source-side 本走 gate の授権

旧 `b03` (v) は再発行時に削除されている。一方、pubcore v2 §10.2 は、同文書が source の admission に条件を追加しないと明記する。このため、D291 の `source_main_run_gate = not_implemented` を、直ちに接続権限と解釈するのは強すぎる。

推奨は新しい D を fold し、次を明文化することである。

1. gate の規範的根拠は pubcore 文書ではなく、Q1(a) のユーザー裁定と新 D である。
2. gate は source core の科学的 `main_admission` 定義を変更しない。
3. pubcore 文書そのものを source の入力として要求しない。
4. canonical publication ledger に予約が存在するかを、送信直前の運用 precondition として検査する。
5. 成功しても submission authority は付与しない。
6. D292 の pilot/main 禁止は別条件として常に残る。
7. gate は deny を追加するだけで、禁止を解除しない。

この解釈を新 D が承認しない場合、§10.2 との抵触は解消せず、(iii) は裁定パッケージに戻す。その場合でも (i)・(ii)・(iv)・(iv-b) は独立して land できる。

## 8. D292 との整合

命名・型・report 表現で次を禁止する。

- `is_submission_allowed`
- `ready_for_main`
- `admitted`
- `approval_complete`
- `can_submit`
- 成功を `True` で返す API
- report の `status: ready`

代わりに、成功時も次を明示する。

```json
{
  "reservation_precondition": "satisfied",
  "submission_authority": "not_granted",
  "pilot_submission": "forbidden",
  "main_submission": "forbidden"
}
```

resolver が返すのは「D291 が blob role を承認した」という事実だけであり、submission approval ではない。実装完了、manifest 完成、report の成功、reservation の存在はいずれも D292 の解除条件にしない。

## 9. テスト計画

### 9.1 台帳

| nodeid | 期待 |
|---|---|
| `test_t793_publication_ledger.py::test_canonical_empty_publication_ledger_is_valid_but_unreserved` | 空 tracked file を正しく読む。 |
| `...::test_reserve_next_publication_appends_one_canonical_entry` | canonical ordinal 1 を一件だけ追加する。 |
| `...::test_publication_ledger_rejects_caller_selected_root_kind_or_path` | 偽 root/kind/path を拒否する。 |
| `...::test_publication_ledger_rejects_duplicate_logical_entry` | 同じ tuple の二行を拒否する。 |
| `...::test_publication_ledger_rejects_noncanonical_jsonl` | key 追加、duplicate key、LF 欠落を拒否する。 |
| `...::test_publication_ledger_rejects_delete_and_recreate_history` | row 追加後の削除・再作成を拒否する。 |
| `...::test_missing_canonical_ledger_is_not_treated_as_empty` | file 不存在を空台帳として受理しない。 |
| `...::test_publication_and_primary_tuple_spaces_must_be_disjoint` | synthetic primary に同 tuple を置くと失敗する。 |

### 9.2 marker/fold

| nodeid | 期待 |
|---|---|
| `test_spool_fold.py::test_plan_fold_accepts_resolved_approved_blob` | marker のない固定 blob を持つ approval fragment が通る。 |
| `...::test_plan_fold_rejects_approval_target_with_unresolved_marker` | fragment 自体ではなく、固定先 blob に marker がある場合に落ちる。 |
| `test_check_docs.py::test_spool_guard_reports_unresolved_approval_marker` | `check_docs` 経由でも同じ違反を報告する。 |
| `test_t793_publication_gates.py::test_unpinned_explanatory_marker_does_not_trigger_gate` | 承認対象でない説明文まで誤拒否しない。 |

### 9.3 source precondition

新 D の fold 後に有効化する。

| nodeid | 期待 |
|---|---|
| `test_t793_publication_gates.py::test_source_main_precondition_returns_non_authorizing_witness` | exact 一件の reservation で witness を返すが、authority は `not_granted`。 |
| `...::test_source_main_precondition_rejects_empty_ledger` | 空ファイルで拒否。 |
| `...::test_source_main_precondition_rejects_duplicate_or_wrong_reservation` | 重複・偽 root/kind を拒否。 |
| `...::test_source_main_precondition_never_reports_submission_allowed` | public object/JSON に allow/ready/admitted field がない。 |

### 9.4 D291 resolver/report

| nodeid | 期待 |
|---|---|
| `test_t793_publication_approval.py::test_loads_canonical_d291_from_fold_commit` | 実 `F_p` と固定 digest から parse できる。 |
| `...::test_d291_rejects_unknown_or_missing_top_level_key` | top-level key の追加・欠落を拒否。 |
| `...::test_d291_rejects_unknown_nested_document_relation_key` | relation の未知 nested key を拒否。 |
| `...::test_d291_rejects_changed_document_relations_note` | 選択 field だけでなく節全体を比較して落とす。 |
| `...::test_d291_rejects_tenth_value_projection_mapping` | `<->` の追加行を拒否。 |
| `...::test_d291_rejects_malformed_list_or_triple_quote` | bracket/triple-quote grammar の緩みを拒否。 |
| `...::test_d291_rejects_self_consistent_manifest_not_derived_from_fp` | manifest 内で整合していても `F_p` と違えば拒否。 |
| `...::test_resolve_d291_role_rejects_wrong_blob_digest` | role/path が同じでも digest 違いを拒否。 |
| `...::test_future_addendum_p_is_relation_but_not_approved_blob` | P draft を承認済み role と誤報しない。 |
| `...::test_approval_report_keeps_d292_forbidden_state` | report が pilot/main forbidden を維持。 |

### 9.5 Addendum P exact-key

| nodeid | 期待 |
|---|---|
| `test_t793_publication_gates.py::test_addendum_p_accepts_exact_p01_p02_p03_fields` | exact 三 field を受理。 |
| `...::test_addendum_p_rejects_extra_p04_field` | extra field を拒否。 |
| `...::test_addendum_p_rejects_missing_p03_field` | 欠落を拒否。 |
| `...::test_addendum_p_rejects_duplicate_p02_field` | 重複を拒否。 |

既存 `test_t139_preregistration_binding.py` は変更せず、A envelope の受理集合にも影響させない。

## 10. 恒真性の検査

| gate | gate がない実装でも通り得る入力 | 赤を保証するテスト |
|---|---|---|
| 固定 root/path/kind | caller が別 path に正しい形の JSONL を置く | `test_publication_ledger_rejects_caller_selected_root_kind_or_path` |
| 一意性 | 同一 tuple を二行記録する | `test_publication_ledger_rejects_duplicate_logical_entry` |
| 非解放 | `empty → row → empty → same row` の Git 履歴 | `test_publication_ledger_rejects_delete_and_recreate_history` |
| primary 互いに素性 | synthetic primary に publication と同一 tuple を置く | `test_publication_and_primary_tuple_spaces_must_be_disjoint` |
| marker | fragment は clean だが固定先 blob に marker がある | `test_plan_fold_rejects_approval_target_with_unresolved_marker` |
| source precondition | ledger file は存在するが 0 bytes | `test_source_main_precondition_rejects_empty_ledger` |
| `F_p` trust root | 偽 manifest が内部的には path/commit/sha 整合 | `test_d291_rejects_self_consistent_manifest_not_derived_from_fp` |
| relations 全体一致 | approved blob triple は同じだが `note` に一文字追加 | `test_d291_rejects_changed_document_relations_note` |
| P exact-key | `p01,p02,p03,p04` を持つ envelope | `test_addendum_p_rejects_extra_p04_field` |
| D292 deny-only | reservation と role 解決の双方が成功 | `test_source_main_precondition_never_reports_submission_allowed` と report test |

実在データが偶然 disjoint、marker-free、重複なしであることだけを正例にすると gate は恒真になり得る。そのため負例は synthetic repository/history/blob を構成し、各不変条件だけを一つずつ破る。

## 11. land 2 branch との衝突境界

`worktree-dev-wave-t139-manifest-w2` と重複し得る API は以下である。

- D291 payload reader
- `source_addendum_b` role 解決
- `document_relations` の model/parser
- D291 role triple の検証

境界は次のように固定する。

1. D291 固有 parser の所有者を `orchestrator/publication/approval_d291.py` の一つだけにする。
2. land 2 の D282 parser `orchestrator/preregistration/approval_payload.py` は変更しない。
3. land 2 が D291 の `source_addendum_b` を必要とする場合、`resolve_d291_role()` または `require_d291_projection_exact()` を import する。
4. T-793 側から preregistration resolver、manifest、snapshot、receipt を変更しない。
5. `BlobRef` は既存型を利用するが `blobref.py` 自体は変更しない。
6. T-793 を先に main へ統合し、land 2 はその後に shared D291 API へ寄せる。両 branch に独立した D291 grammar を作らない。

次は land 2 と重複しない。

- publication ledger
- P envelope exact-key
- approval marker spool gate
- source reservation precondition
- publication report CLI

## 12. 実装順序

1. 空 publication 台帳と `ledger.py`、台帳テスト。
2. `approval_d291.py` と grammar/trust-root テスト。
3. `addendum_p_envelope.py` と exact-key テスト。
4. `approval_guard.py` を作り、`spool_fold._discover()` に結線。
5. direct fold と `check_docs` の統合テスト。
6. deny-only `report.py`。
7. 新 D の裁定・fold。
8. 裁定が通った場合だけ `admission.py` とそのテスト。
9. 実装子から返却後、親が規定の検査を実行する。実装子は docs を編集せず、commit もしない。

## 総括

**判定: NO-GO（現状の 1 wave 一括完結）。**

理由は、(iii) の source-side gate が旧 `b03` (v) から削除され、pubcore v2 §10.2 が source admission への条件追加を否定しているのに対し、既存 decision はこの衝突の解釈を確定していないためである。新 D が「source の科学的 admission ではなく、deny-only の送信前運用 precondition」として授権すれば GO に切り替えられる。

親 brief の provisional 裁定への評価は以下である。

- **P1: 賛成。** 固定パス `output/registry/t139-publication-reservations.jsonl` を唯一の台帳とする。
- **P2: 条件付き賛成。** `orchestrator/publication/` への分離は正しい。`__init__.py` と fold 共通用 `approval_guard.py` を追加する。preregistration package は変更しない。
- **P3: 賛成。** reservation entry は発行しない。不存在ではなく、0-byte の tracked ledger を採用する。
- **P4: そのままでは反対。** 新 D が必要であり、API 名も `require_source_main_publication_reservation_precondition()` に変える。成功は submission を授権しない。
- **P5: 反対。** `check_docs` だけでは direct fold を止められない。`spool_fold._discover()` の共有 validation に結線する。
- **P6: 賛成。** 純粋な構造化 report と決定的 JSON CLI にする。ただし `submission_authority="not_granted"` と D292 の forbidden 状態を常に含める。

新 D が同 wave 中に fold されない場合は、(iii) の `admission.py` と接続テストを落とし、(i)・(ii)・(iv)・(iv-b)、空台帳、deny-only report を残す。これらは D292 の投入禁止を一切解除せず、独立して閉じられる。