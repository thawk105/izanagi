# 段 1 brief 付録 — `DW-O09` 凍結 bytes の pin 閉包 (実測)

対象 A = `output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json`
対象 B = `output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md`

## 機械的に検査している pin は 1 本の trust root chain だけである

```text
docs/decisions.md ## D282 (台帳 = trust root の正本)
  └─ orchestrator/preregistration/approval_payload.py (parser + trust root pin)
       └─ orchestrator/tests/test_t139_approval_payload.py (literal 三つ組の test pin)
```

| path:line | pin の型 | 内容 |
|---|---|---|
| `docs/decisions.md:12911-12914` | path pin + digest pin | 対象 B の三つ組 (`sha256 = 61ba2f8b...a480`) |
| `docs/decisions.md:12915-12918` | path pin + digest pin | 対象 A の三つ組 (`sha256 = d541ccd5...b047e`) |
| `docs/decisions.md:12925-12928` | 排他 pin | `not_approved_as_record_items_root` (旧 `record-items.md` を role から除外) |
| `docs/decisions.md:12929-12939` | exact key pin | `operational_boundary` |
| `orchestrator/preregistration/approval_payload.py:17-21` | **trust root pin** | `D282_DECISIONS_REF` = `docs/decisions.md` を**固定 commit `39d76098...` + sha256** で pin する |
| `orchestrator/preregistration/approval_payload.py:23-32` | role key pin | `APPROVED_BLOB_ROLES` に `record_items` / `receipt_schema` |
| `orchestrator/preregistration/approval_payload.py:461-495` | 閉包検査 | `approved_blobs` が **exact 6 role** でなければ拒否 |
| `orchestrator/tests/test_t139_approval_payload.py:36-44` | literal test pin | 対象 A・B の path/commit/sha256 |

## 本 wave にとって決定的な帰結 3 点

1. **本 decision を `docs/decisions.md` へ追記しても trust root は壊れない。**
   `D282_DECISIONS_REF` は**固定 commit の blob** を pin しており、`blobref.read_pinned_blob` は
   その履歴 commit の tree から読む。作業木の bytes は検査対象ではない
   (D234 決定 (6) 「現在の作業木の bytes を固定する検査は置かない」がそのまま効いている)。
   → **fold 後に `docs/decisions.md` が伸びても、既存 pin も既存 test も赤にならない。**
2. **`d282_record_approval` / `d291_publication_approval` はコードにも台帳にも実在しない。**
   `output/insights/2026-08-11_t139-manifest-land2-s2/` の**未裁定の設計提案の散文** 3 件だけである。
   → Q2 の envelope は**既存 consumer を 1 つも壊さない新規契約**である。逆に言えば、
   本 decision が書くまで consumer 側の実装契約は存在しない。
3. **`orchestrator/publication/` (D291 系) は対象 A・B を一切参照しない。**
   D291 は `publication-core-v2.md` / `addendum-b-v2.md` を pin する並行 trust root であり、
   両者は別の module (`approval_d291.py` vs `approval_payload.py`) に分かれている。
   → Q2 の「2 区画の envelope」は、既に module 境界として実在する分割を manifest 側へ写すものである。

## 既存の公開 API (envelope の consumer 契約を書くときの実在 seam)

```text
orchestrator/preregistration/approval_payload.py
  load_approval_payload(repository_root) -> ApprovalPayload
orchestrator/preregistration/blobref.py
  read_pinned_blob(repository_root, ref: BlobRef) -> bytes
orchestrator/preregistration/erratum.py
  compose_core(repository_root, *, core_ref, erratum_refs, expected_composed_sha256) -> ComposedCore
orchestrator/publication/approval_d291.py
  load_d291_payload(repository_root) -> _D291ApprovalPayload
  require_d291_projection_exact(repository_root, projection) -> None
  resolve_d291_approvals(repository_root) -> dict[ApprovedRoleName, _D291RoleResolution]
```

**D305 の制約が効いている** — `approval_d291.py` には単一 role を解決する公開 API が意図的に無く、
payload 全体を `exact_closure` で検証してから role → 状態の写像を一括で返す形である。
Q2 (a) の「root は role からの内部固定写像」はこの形と整合する。

## 見つからなかったもの

- `FROZEN_MANIFEST` は T-139 の scope に無い (別 task T-080 の識別子)。
- 対象 A・B の digest を literal で持つのは上表の 2 箇所だけ。他 60 件超はすべて
  `output/insights/**` と過去 worklog の散文であり、コードからも test からも読まれない。
