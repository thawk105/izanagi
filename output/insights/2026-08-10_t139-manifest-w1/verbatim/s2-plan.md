結論から言うと、U1〜U6 全体を 1 wave に安全に収めるのは無理があります。静的見積りは production 約 5,300〜7,200 行、test 約 3,600〜5,000 行です。特に U3 の完全 schema と U5 の land transaction が大きく、前 wave の規模懸念を裏付けます。

指定されたファイルはすべて読めました。以下は実ファイルの現在行に基づく計画です。編集・pytest 実行はしていません。

## 先に固定すべき解釈

二点、実装前に正規化が必要です。

- 親 brief は第 2 erratum を未承認とし、承認集合を erratum-1 のみとしています（[s1-brief.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s1-brief.md:52)）。一方、D263 の理由欄には「第 2 erratum が既に承認済み」とあります（[decisions.md:12173](/work/1/SFC/tanab/izanagi/docs/decisions.md:12173)）。後者は blob identity を持たない説明文なので承認根拠に使わず、manifest の exact set を唯一の権威にします。新 decision fragment で「registry 登録可能性と承認 membership は別」と明記します。
- 現在の land lock は Git common dir 内の lock です（[dev_wave_land.py:1272](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:1272)）。したがって linked worktree 間は直列化できますが、独立 clone の lock 同士は物理的には共有されません。U5 の clone 防止保証は「指定された一つの canonical main と、その trusted consumer だけが権威」という運用境界を必須前提にします。任意 clone の local main まで権威とするなら、P4 だけでは不可能で、remote/shared CAS など別裁定が必要です。

## U1 — 承認 manifest

### 形式と trust chain

次の三段 commit にします。

1. artifact commit `A`: record-items 再発行、schema、第 2 erratum draft、alpha request、空 ledger を追加。
2. manifest commit `M`: `A` の各 blob を `(path, commit, sha256)` で pin。`approval_fold_commit` は literal に `dce4ae4fed6f4fb33747165c5b92c16d01822850`。
3. gate commit `G`: code 内の `TRUSTED_T139_MANIFEST_REF` が manifest blob `(path, M, sha256)` を pin。

これで caller が manifest ref、承認 erratum 集合、schema refを選ぶ入口を作りません。v1 は後から編集せず、第 2 erratum 承認時は v2 を再発行します。

manifest v1 は少なくとも次を exact key で持ちます。

- core、追補 A、derivation map
- record-items 再発行版
- receipt schema
- `approval_fold_commit = F_e`
- `approved_errata = [t139-core-s15-exactkey-v1]`
- `erratum_application_order` も同じ 1 件
- `composed_sha256 = d1782...de82`
- 第 2 erratum は `draft_errata` に置き、承認集合へ入れない
- 旧 record-items と旧追補 A を `superseded_blobs` に置く
- alpha ledger genesis、予約 request、family root、ordinal

### ファイルと見積り

| ファイル | 新規/既存・挿入位置 | 主な署名 | production | test |
|---|---|---|---:|---:|
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/t139_approval_manifest_v1.json` | 新規、1 行目から | 1 枚の closed JSON object | 90〜130 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/manifest.py` | 新規、1 行目から | 下記 | 300〜420 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/_strict_json.py` | 新規、1 行目から | `strict_json_loads`, `canonical_json_bytes` | 120〜170 | — |
| `/work/1/SFC/tanab/izanagi/output/insights/2026-08-10_t139-manifest-w1/README.md` | 新規 | blob/commit topology と非承認状態 | 35〜55 | — |
| `/work/1/SFC/tanab/izanagi/docs/spool/decisions/2026-08-10-dev-wave-t139-manifest-w1-1.md` | 新規 | D263 の説明誤り、manifest exact set、D264 境界 | 55〜80 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/tests/test_t139_approval_manifest.py` | 新規 | 実 manifest と synthetic manifest | — | 320〜430 |

署名は次の形です。

```python
@dataclass(frozen=True)
class ApprovedErratumRef:
    erratum_id: str
    blob: BlobRef
    approval_fold_commit: str

@dataclass(frozen=True)
class DraftErratumRef:
    erratum_id: str
    blob: BlobRef
    status: Literal["draft_unapproved"]

@dataclass(frozen=True)
class ApprovalManifest:
    manifest_ref: BlobRef
    approval_fold_commit: str
    target_core: BlobRef
    addendum_a: BlobRef
    derivation_map: BlobRef
    record_items: BlobRef
    receipt_schema: BlobRef
    approved_errata: tuple[ApprovedErratumRef, ...]
    erratum_application_order: tuple[str, ...]
    composed_sha256: str
    draft_errata: tuple[DraftErratumRef, ...]
    alpha_reservation: AlphaReservationContract

def parse_approval_manifest(blob: bytes) -> ApprovalManifest: ...

def load_approval_manifest(
    repository_root: str | os.PathLike[str],
) -> ApprovalManifest: ...
```

`load_approval_manifest` は manifest ref を引数に取りません。実 manifest commit が `F_e` の子孫で、manifest・承認 blob・`F_e` が measurement HEAD の祖先であることも検査します。

U1 見積りは production 600〜855 行、test 320〜430 行です。

## U2 — record-items 再発行

元の [record-items.md:121](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-addendum-a/record-items.md:121) は `post_performance_failure` に marker または performance raw を要求します。一方、追補 A の a04 は preflight の a03 失敗も同 reason へ写すため、marker も run も無い正当な失敗が存在します。

再発行版では `attempts[].failure_evidence` を closed tagged union にし、第三分岐を次の形で追加します。

```text
{
  "kind": "a03_environment_observation",
  "environment_observation_ordinal": <positive integer>
}
```

検査条件は以下です。

- ordinal は同じ attempt の `environment_observations[]` を一意に参照する。
- preflight 観測なら `scope == "preflight"` かつ `run_id_or_null == null`。
- pre-run 観測なら対応 run が同じ attempt に属する。
- `failed: true` や `recovered: false` のような自己申告 boolean は置かない。
- validator が `stat_before[]` / `stat_after[]` / malformed 状態から a03 不成立を再計算する。
- observation が正常範囲なのに第三分岐を使った receipt は拒否する。

併せて nested field 表の a12 は「較正 simulation receipt」ではなく「事前固定 stress-check transcript」に訂正し、この evidence だけでは第 2 erratum の承認を代替しないと書きます。

| ファイル | 新規/既存 | production | test |
|---|---|---:|---:|
| `/work/1/SFC/tanab/izanagi/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md` | 新規、元文書を遡及編集しない | 230〜290 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/tests/test_t139_record_items_reissue.py` | 新規 | — | 130〜180 |

テストは、preflight a03 失敗の正例、dangling ordinal、別 attempt 参照、正常観測を失敗扱いする mutant、未知 boolean field を固定します。

## U3 — 受領証 JSON Schema

### 1 blob と保守単位の分割

権威となる物理ファイルは次の 1 枚だけにします。

`/work/1/SFC/tanab/izanagi/orchestrator/preregistration/t139_receipt_schema_v1.json`

外部 `$ref` や生成元 fragment は持たず、Draft 7 の `definitions` で論理分割します。物理 fragment と generated blob の二重正本を避けるためです。

論理区分は次の順です。

1. `primitives`: commit、SHA-256、ID、repo-relative path、時刻、raw pointer
2. `preregistration`: core/addendum/errata/fold commit
3. `environment_checkout`: environment、attestation、measurement checkout、dependency pins
4. `build_arms`: source、compile、binary、toolchain、exec witness
5. `execution`: workload、schedule、planned run、actual run、wait
6. `allocation_evidence`: allocation、phase cap/event、rehash、correctness、liveness
7. `attempt_telemetry`: a03 observation、a04 marker、failure evidence、a13 reservation
8. root: [record-items.md:40](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-addendum-a/record-items.md:40) の exact 18 key

動的 map である `translation_units{}` や `effective_flags{}` は `patternProperties` を使い、それでも `additionalProperties: false` を課します。

Draft 7 で表せない参照整合性は、同じ blob の top-level 拡張 keywordに exact ordered ID として載せます。

```json
"x-izanagi-semantic-checks": [
  "t139-binding-v1",
  "t139-id-foreign-key-v1",
  "t139-schedule-v1",
  "t139-attempt-outcome-v1",
  "t139-a03-failure-evidence-v1",
  "t139-correctness-separation-v1",
  "t139-alpha-reservation-v1"
]
```

未知 ID、欠落、順序違いは schema contract error です。汎用 DSL は作りません。

### nested closure の機械検査

production の schema loader が、schema AST 全体を再帰走査します。

```python
def require_closed_object_schemas(
    document: Mapping[str, object],
) -> None: ...
```

次を全探索します。

- `definitions`
- `properties`
- `patternProperties`
- `items`
- `allOf` / `anyOf` / `oneOf`
- `not`
- `if` / `then` / `else`
- dependencies 内の schema
- internal `$ref` の解決先

`type: object`、object を含む union、または object 用 keyword を持つ全 nodeに対し、`additionalProperties is False` を要求します。外部 `$ref`、未解決 internal ref、schema-valued `additionalProperties` は拒否します。

テストは二重に置きます。

- schema AST 上の全 object が closed であること。
- 完全な正例 fixture の各実在 nested objectへ未知 keyを一つずつ注入し、すべて拒否されること。

### ファイルと署名

| ファイル | 新規/既存 | 主な署名 | production | test |
|---|---|---|---:|---:|
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/t139_receipt_schema_v1.json` | 新規 | Draft 7、1 blob | 1,500〜2,100 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/receipt_schema.py` | 新規 | 下記 | 300〜430 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/tests/test_t139_receipt_schema.py` | 新規 | schema、closure、semantic fixtures | — | 1,000〜1,400 |

```python
class ReceiptSchemaContractError(Exception): ...

@dataclass(frozen=True)
class SchemaViolation:
    json_pointer: str
    validator: str
    schema_pointer: str

@dataclass(frozen=True)
class CompiledReceiptSchema:
    ref: BlobRef
    sha256: str
    document: Mapping[str, object]
    semantic_checks: tuple[str, ...]

def load_receipt_schema(
    repository_root: str | os.PathLike[str],
    *,
    ref: BlobRef,  # resolver が manifest から渡す。公開 gate caller は選べない
) -> CompiledReceiptSchema: ...

def require_closed_object_schemas(
    document: Mapping[str, object],
) -> None: ...

def iter_schema_violations(
    schema: CompiledReceiptSchema,
    instance: object,
) -> tuple[SchemaViolation, ...]: ...
```

U3 は production 1,800〜2,530 行、test 1,000〜1,400 行です。

## U4 — 第 2 erratum と pilot 停止 gate

第 2 erratum は core の [preregistration.md:221](/work/1/SFC/tanab/izanagi/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:221) だけを対象とします。

```text
old_text = "事前 simulation で較正する。\n"
new_text = "事前固定 stress check で評価する。\n"
old_sha256 = 225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89
```

固有 validator は以下を要求します。

- `erratum_id == "t139-core-s7-stresscheck-v1"`
- operation 数 exact 1
- section 7、line 221、固定 anchor
- old text と old digest が実 core bytesに一致
- old full line の出現が core 全体で exact 1
- new text が上の固定 bytes と一致
- erratum-1 の line 404/424 と非重複

既存 validator の `len == 2` や `a01〜a12` token 検査は流用しません。

### 恒真でない停止 gate

```python
_PILOT_REQUIRED_ERRATUM_IDS = frozenset({
    "t139-core-s15-exactkey-v1",
    "t139-core-s7-stresscheck-v1",
})

def _require_pilot_errata_approved(
    manifest: ApprovalManifest,
    *,
    resolved_erratum_ids: tuple[str, ...],
) -> None: ...
```

処理順は次です。

1. `resolved_erratum_ids` が manifest の approved exact set/order と一致するか確認。
2. `_PILOT_REQUIRED_ERRATUM_IDS - approved_ids` を計算。
3. 欠落があれば `PilotErratumApprovalPendingError(missing_erratum_ids=...)`。
4. 欠落がなければ通す。

現 manifest v1 は erratum-1 だけなので必ず停止します。一方、synthetic v2 manifest で第 2 erratum を approved setへ移し、二枚適用後 digestを固定すれば通ります。したがって恒真 deny stubではありません。draft list に存在するだけでは通りません。

`resolve_effective_preregistration` の binding 構築前にこの gate を通し、future `submit_pilot` の実装者が呼び忘れる余地をなくします。`submit_pilot` 自体は作りません。

### ファイルと現在行

| ファイル | 新規/既存・挿入位置 | production | test |
|---|---|---:|---:|
| `/work/1/SFC/tanab/izanagi/output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md` | 新規 | 100〜140 | — |
| [erratum.py:20](/work/1/SFC/tanab/izanagi/orchestrator/preregistration/erratum.py:20) | 既存。固定文字列を現 21 行目後、validator を現 357 行目直前、registry を現 360 行目へ追加 | 90〜125 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/pilot_gate.py` | 新規 | 80〜110 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/tests/test_t139_stresscheck_gate.py` | 新規 | — | 220〜300 |

U4 は production 270〜375 行、test 220〜300 行です。

## U5 — a13 原子予約台帳

### 台帳と行形式

台帳 path は次に固定します。

`/work/1/SFC/tanab/izanagi/docs/t139-primary-alpha-reservations.jsonl`

artifact commitでは 0 byte の tracked fileとして作成し、最初の実予約は final land の post-land commitだけが追記します。

予約 request:

`/work/1/SFC/tanab/izanagi/orchestrator/preregistration/t139_alpha_reservation_request_v1.json`

JSONL の各行は UTF-8、compact sorted-key JSON、末尾 LF 1 個です。

```json
{"family_root":"88d68f9127b31df5aafc3d59607896626a1652e8","ordinal":1,"request_commit":"<40 lowercase hex>","request_path":"orchestrator/preregistration/t139_alpha_reservation_request_v1.json","request_sha256":"<64 lowercase hex>","schema_version":"izanagi-primary-alpha-reservation-v1","study_id":"T-139"}
```

`reservation_entry_sha256` はこの canonical JSON bytesと末尾 LFを合わせた一行全体の SHA-256 とします。`reservation_commit` はその行を書いた post-land commit SHAであり、自己参照を避けるため行内には入れません。

### create-only の機械保証

```python
@dataclass(frozen=True)
class AlphaReservationRequest: ...

@dataclass(frozen=True)
class AlphaReservationEntry: ...

@dataclass(frozen=True)
class AlphaReservationPlan:
    status: Literal["append", "already_reserved"]
    ledger_path: str
    before_sha256: str
    after_sha256: str
    after_bytes: bytes
    entry_sha256: str

@dataclass(frozen=True)
class AlphaReservationEvidence:
    ledger_path: str
    family_root: str
    ordinal: int
    reservation_entry_sha256: str
    reservation_commit: str

def parse_alpha_ledger(blob: bytes) -> tuple[AlphaReservationEntry, ...]: ...

def plan_t139_alpha_reservation(
    repository_root: str | os.PathLike[str],
    *,
    manifest: ApprovalManifest,
) -> AlphaReservationPlan: ...

def resolve_t139_alpha_reservation(
    repository_root: str | os.PathLike[str],
    *,
    measurement_head: str,
    manifest: ApprovalManifest,
) -> AlphaReservationEvidence: ...
```

`parse_alpha_ledger` は次を拒否します。

- CR、NUL、blank line、末尾 LF 欠落
- duplicate JSON key、非 canonical key/order/spacing
- unknown/missing field
- `(family_root, ordinal)` 重複
- `study_id` 重複
- ordinal の不正値
- symlink、非 regular file、size超過

plan は `after_bytes == before_bytes + one_canonical_line` だけを作ります。同じ request が既にある場合だけ idempotent、同じ pairを別 request/study が占めていれば conflictです。失敗・中断でも削除・再利用はしません。

### land lock への配線点

既存の spool fold transaction state は全 `targets` の before/after digestと after bytesを保存しています（[spool_fold.py:1928](/work/1/SFC/tanab/izanagi/tools/spool_fold.py:1928)）。そのため別の alpha transaction stateを作らず、ledger appendを同じ `FoldPlan.targets` に追加します。

配線は次です。

- [spool_fold.py:1905](/work/1/SFC/tanab/izanagi/tools/spool_fold.py:1905) の直後に、予約 targetを FoldPlanへ合成して transaction IDを再計算する `with_t139_alpha_reservation(plan, reservation)` を追加。
- [dev_wave_land.py:1628](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:1628) の `_load_spool_fold` 後に、同じ checkoutの alpha moduleを安全にロードする `_load_alpha_ledger()` を追加。
- land lock取得後の [dev_wave_land.py:2257](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:2257) で docs planとalpha planを作り、現在の 2260 行目で path集合を確定する前に一つの planへ合成。
- [dev_wave_land.py:2275](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:2275) の collision検査、[dev_wave_land.py:2363](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:2363) の snapshot、既存 state、rollbackへledger pathを含める。
- 実変更は現在の [dev_wave_land.py:1872](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:1872) の一回の `fold.apply_fold()`だけ。state永続化後にdocsとledgerを適用し、同じ index・commit・rollback境界に置く。
- 初回予約時は U1 の decision fragmentが必須なので、alpha appendだけの誤った “documentation fold” commitは作らない。active stateからの recoveryは既存 [dev_wave_land.py:2194](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:2194) 経路で再開。
- [git_state.py:561](/work/1/SFC/tanab/izanagi/tools/dev_waves/git_state.py:561) で、landed wave commitによる ledger の M/D を fold-owned pathとして拒否。
- [git_state.py:909](/work/1/SFC/tanab/izanagi/tools/dev_waves/git_state.py:909) の post-land diff検査では、parent blobからchild blobへの exact one-line appendだけを許す。
- [operations.md:125](/work/1/SFC/tanab/izanagi/docs/dev-wave/operations.md:125)〜現 130 行を置換し、docs foldとalpha予約が同じlock/state/commitであることを記録。
- [docs/README.md:26](/work/1/SFC/tanab/izanagi/docs/README.md:26) の直前にledger索引を2行追加。

`LandRequest` と CLI に family root、ordinal、ledger pathを追加しません。すべて pinned manifest/requestから導出します。

### clone 間での差

防げない設計は、各 clone がそれぞれ local refを CAS 更新する形です。clone A/Bの双方が自分の ref上で `(F,1)` を初回予約でき、それぞれの local validatorが一件だけを見て通します。

提案設計では、clone/wave は予約 requestを持つだけで、予約 commitを自分で作れません。指定された canonical main に対してのみ `dev_wave_land` を実行し、最初の land が lock内で ledgerを更新します。二番目の waveは、その post-land commitを含まないため stale mainとして ffできません。canonical mainを取り込み直すと、同じ pairが既に存在するため conflict、同一 requestなら idempotentになります。receiptの `reservation_commit` も canonical main historyから resolverが導出した値との一致を要求します。

ただし、独立 clone自身の mainを「別の canonical main」と称することまで、現在の common-dir lockでは防げません。trusted consumerが一つの canonical mainだけを権威とする境界が必要です。それを認めない要件なら、共有CAS/remote serviceを追加する別裁定が必要です。

### ファイルと見積り

| ファイル | 新規/既存・挿入位置 | production | test |
|---|---|---:|---:|
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/alpha_ledger.py` | 新規 | 360〜480 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/t139_alpha_reservation_request_v1.json` | 新規 | 10〜16 | — |
| `/work/1/SFC/tanab/izanagi/docs/t139-primary-alpha-reservations.jsonl` | 新規、0 byte genesis | 0 | — |
| [spool_fold.py:1905](/work/1/SFC/tanab/izanagi/tools/spool_fold.py:1905) | 既存、plan合成 helper | 55〜85 | — |
| [dev_wave_land.py:1628](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:1628) | 既存、loader/planning/recovery配線 | 170〜240 | — |
| [git_state.py:561](/work/1/SFC/tanab/izanagi/tools/dev_waves/git_state.py:561) | 既存、fold-owned/strict append検査 | 90〜130 | — |
| [operations.md:125](/work/1/SFC/tanab/izanagi/docs/dev-wave/operations.md:125) | 既存、現行節を圧縮置換 | 4〜8 | — |
| [docs/README.md:26](/work/1/SFC/tanab/izanagi/docs/README.md:26) | 既存、索引 | 2 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/tests/test_t139_alpha_ledger.py` | 新規 | — | 300〜400 |
| [test_spool_fold.py:1212](/work/1/SFC/tanab/izanagi/orchestrator/tests/test_spool_fold.py:1212) | 既存、transaction resume test前に追加 | — | 100〜150 |
| [test_dev_wave_land.py:2123](/work/1/SFC/tanab/izanagi/orchestrator/tests/test_dev_wave_land.py:2123) | 既存、lock内fold test直後 | — | 350〜480 |
| [test_dev_waves_git_state.py:305](/work/1/SFC/tanab/izanagi/orchestrator/tests/test_dev_waves_git_state.py:305) | 既存、direct-child shape test後 | — | 140〜200 |

U5 は production 700〜965 行、test 890〜1,230 行です。

## U6 — resolver、PreregBinding、verify_receipt

### 三公開面

U6 は実質「関数2つ＋データ型1つ」です。

```python
@dataclass(frozen=True, init=False)
class PreregBinding:
    manifest_ref: BlobRef
    approval_fold_commit: str
    core: BlobRef
    addendum_a: BlobRef
    addendum_b: BlobRef | None
    derivation_map: BlobRef
    record_items: BlobRef
    receipt_schema: BlobRef
    errata: tuple[ApprovedErratumBinding, ...]
    composed_core_sha256: str
    measurement_head: str
    alpha_reservation: AlphaReservationEvidence

def resolve_effective_preregistration(
    repository_root: str | os.PathLike[str],
) -> PreregBinding: ...

def verify_receipt(
    repository_root: str | os.PathLike[str],
    *,
    binding: PreregBinding,
    receipt_path: str | os.PathLike[str],
) -> ReceiptVerification: ...
```

`PreregBinding` は public constructorを持たせず、resolverの private factoryだけが生成します。`repository_root` は checkoutの場所であって、manifest/schema/expected setの権威ではありません。`measurement_head` は実 checkoutから導出します。

### structured reason 型

```python
class ReceiptReasonCode(StrEnum):
    RECEIPT_IO = "receipt_io"
    RECEIPT_SYMLINK = "receipt_symlink"
    RECEIPT_SIZE = "receipt_size"
    RECEIPT_JSON = "receipt_json"
    RECEIPT_SCHEMA = "receipt_schema"
    BINDING_MISMATCH = "binding_mismatch"
    DANGLING_REFERENCE = "dangling_reference"
    SCHEDULE_MISMATCH = "schedule_mismatch"
    ATTEMPT_OUTCOME_MISMATCH = "attempt_outcome_mismatch"
    A03_FAILURE_EVIDENCE_MISMATCH = "a03_failure_evidence_mismatch"
    CORRECTNESS_SEPARATION_MISMATCH = "correctness_separation_mismatch"
    ALPHA_RESERVATION_MISMATCH = "alpha_reservation_mismatch"

@dataclass(frozen=True)
class ReceiptReason:
    code: ReceiptReasonCode
    stage: str
    json_pointer: str | None
    context: tuple[tuple[str, str | int | bool | None], ...]

@dataclass(frozen=True)
class ReceiptVerification:
    status: Literal["accepted", "rejected"]
    receipt_sha256: str | None
    reasons: tuple[ReceiptReason, ...]

    def __bool__(self) -> NoReturn:
        raise TypeError("ReceiptVerification を bool として使ってはならない")
```

受領証の不正は例外へ潰さず、決定順の `reasons` として返します。acceptedなら reasonsは空、rejectedなら1件以上です。

### fail-closed の分岐

| 検査 | 失敗時 |
|---|---|
| repository root、HEAD、Git metadata | `RepositoryResolutionError` |
| trusted manifest blobの解決・digest | `ApprovalManifestResolutionError` |
| manifest duplicate/unknown/missing key、exact set/order | `ApprovalManifestContractError` |
| `F_e`、manifest、各 approved blobの祖先関係 | `ApprovalAncestryError` |
| core/addendum/record/schema blob不在・digest不一致 | `ApprovedBlobResolutionError(component=...)` |
| erratum parse、未知ID、固有validator、non-overlap、composed digest | `PreregistrationCompositionError`。既存 `ErratumError` を causeとして保持 |
| addendum exact-13/envelope不一致 | `AddendumResolutionError`。既存 `AddendumEnvelopeError` を causeとして保持 |
| 第 2 erratum未承認 | `PilotErratumApprovalPendingError` |
| schema自体のDraft不正、open nested object、未知semantic ID、jsonschema package不在 | `ReceiptSchemaContractError` |
| canonical ledgerが読めない、historyに予約transitionがない、ledger自身が重複 | `AlphaLedgerAuthorityError` |
| forged/stale `PreregBinding`、private factory invariant不成立 | `InvalidPreregBindingError` |
| verifier実装の未知分岐・reasonなしreject | `ReceiptVerifierContractError` |

`verify_receipt` の入力側については次の区別をします。

- receiptの不在、symlink、非regular、size超過、JSON不正、schema違反、binding自己申告不一致、alpha証拠不一致は `ReceiptReason`。
- trusted schemaやcanonical ledgerそのものを確立できない場合は例外。receipt側の責任に見せかけません。
- receiptは `O_NOFOLLOW` で一度だけ開き、同じ fdのbyte bufferからhashとstrict JSON parseを行います。
- schema検査後に semantic checkを行い、構造違反から大量の派生理由を作らないようstage単位で打ち切ります。

本 wave の `verify_receipt` は receipt自体、binding、cross-field整合性を検査します。trace-enabled correctness verifierの実行や certified eligibility判定は行いません。前 wave裁定どおり、correctness verifierは `submit_pilot` と同じ次 waveの削れない要件です。

### D264 契約

現在この契約を固定しているのは [test_t139_preregistration_binding.py:512](/work/1/SFC/tanab/izanagi/orchestrator/tests/test_t139_preregistration_binding.py:512) の `test_module_exports_no_admission_api` です。package facadeの `__all__` と属性から四名前を排除し、docstringの「本 module は投入 gate ではない」を検査しています。

U6 でもこの境界は変えません。

- package facadeと既存三つの純関数 moduleは引き続き非gate。
- `resolve_effective_preregistration`、`PreregBinding`、`verify_receipt` は新規の明示的な `orchestrator.preregistration.gate` からだけ利用。
- package rootへ再exportしない。
- `submit_pilot` はどこにも実装・exportしない。
- 現 docstring の「本 waveでは実装しない」という時間依存部分だけを、「gateは専用submoduleに隔離する」へ変更する。

したがって D264 の非gate契約自体は変更不要です。もし package rootから三名前をexportする設計を採るならD264変更が必要ですが、本案では採りません。

### ファイルと現在行

| ファイル | 新規/既存・挿入位置 | production | test |
|---|---|---:|---:|
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/binding.py` | 新規 | 180〜240 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/resolver.py` | 新規 | 430〜570 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/receipt.py` | 新規 | 650〜850 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/preregistration/gate.py` | 新規、explicit facade | 50〜80 | — |
| [blobref.py:135](/work/1/SFC/tanab/izanagi/orchestrator/preregistration/blobref.py:135) | 既存。`read_pinned_blob` 後、現 `_git_env` 前に HEAD/ancestor/unpinned commit-blob helper | 160〜220 | — |
| [__init__.py:1](/work/1/SFC/tanab/izanagi/orchestrator/preregistration/__init__.py:1) | 既存、docstring現1〜6行のみ。export集合は維持 | 3〜5 | — |
| [blobref.py:1](/work/1/SFC/tanab/izanagi/orchestrator/preregistration/blobref.py:1) | 既存、docstring現1〜6行 | 3〜5 | — |
| [erratum.py:1](/work/1/SFC/tanab/izanagi/orchestrator/preregistration/erratum.py:1) | 既存、docstring現1〜6行 | 3〜5 | — |
| [addendum_envelope.py:1](/work/1/SFC/tanab/izanagi/orchestrator/preregistration/addendum_envelope.py:1) | 既存、docstring現1〜6行 | 3〜5 | — |
| `/work/1/SFC/tanab/izanagi/orchestrator/tests/test_t139_preregistration_gate.py` | 新規 | — | 850〜1,150 |
| [test_t139_preregistration_binding.py:512](/work/1/SFC/tanab/izanagi/orchestrator/tests/test_t139_preregistration_binding.py:512) | 既存。facade非exportを維持し、専用gateのexact exportとsubmit不在を追加検査 | — | 20〜30 |

U6 は production 1,480〜1,980 行、test 870〜1,180 行です。

## 全体規模と分割案

重複を除いた見積りです。

| 単位 | production | test |
|---|---:|---:|
| U1 | 600〜855 | 320〜430 |
| U2 | 230〜290 | 130〜180 |
| U3 | 1,800〜2,530 | 1,000〜1,400 |
| U4 | 270〜375 | 220〜300 |
| U5 | 700〜965 | 890〜1,230 |
| U6 | 1,480〜1,980 | 870〜1,180 |
| 合計 | **5,080〜6,995** | **3,430〜4,720** |

周辺fixtureやmutation testの増分を含めると、現実的な上側は production 約7,200、test 約5,000行です。

1 waveへ押し込まず、最低でも次の三つの未land sliceに分けるのが安全です。

1. Contract/artifact slice: U2、U3、第2 erratum文書とvalidator、alpha request/空ledger/純parser。
2. Authority slice: U1、pilot approval gate、U6。
3. Land transaction slice: U5 の spool/land/git-state/recovery 配線。

三 sliceとも単独landせず、次の producer waveと合わせて一回だけlandします。ただし、これは Q-D の「2波」を実質的に再解釈するので、実行前にユーザー裁定へ戻す必要があります。

削れるものは、汎用 multi-study alpha CLI、schema生成DSL、remote CAS、receipt writer、durable submission intent、PBS、driver、collector、addendum B、main submission、certified consumerです。ただし receipt writer・intent・collector・correctness verifierは `submit_pilot` と同じ次 waveでは再び必須になります。

## 総括

- 削れない最小集合は、manifest authority、record-items第三分岐、1 blob完全schemaと全nested closure検査、非恒真pilot gate、canonical ledgerのstrict append/rollback、resolver/binding、structured-reason verifier、D264境界テストです。
- 最大の技術的riskは U5 です。既存 land の transaction/recovery/declared-commit形状を壊さずledgerを同じcommitへ入れる必要があり、さらに独立cloneに対する保証は「一つのcanonical mainだけが権威」という境界に依存します。次点は U3 のnested schema完全性です。
- 1 wave収容判定は **不可**です。最低三つの未land実装sliceへ分け、Q-D再解釈としてユーザー裁定へ返すのが妥当です。