## 0. 予算判定（最優先）

`wc -l orchestrator/submission_gate/*.py` の実測は **5,974行**。

| file | 現在行数 |
|---|---:|
| `_attempt_authority.py` | 845 |
| `_binding.py` | 261 |
| `_event_chain.py` | 156 |
| `_git.py` | 753 |
| `_manifest.py` | 341 |
| `_receipt_io.py` | 164 |
| `_receipt_schema.py` | 186 |
| `_safe_io.py` | 541 |
| `_semantic_validator.py` | 2,720 |
| その他 | 7 |
| 合計 | **5,974** |

D509上限6,200行に対する残余は **226行**。

名目上の単位5見積りは次のとおり。

| production変更 | 予定位置 | 純増見積り |
|---|---|---:|
| writer新規 | `orchestrator/submission_gate/_writer.py:new:1-112` | 90〜112 |
| vector digest field | `_manifest.py:147-149,151-198,208-226` | 8〜16 |
| pointer検査 | 既存実装を再利用 | 0 |
| safe atomic I/O | 既存実装を再利用 | 0 |
| vector JSON・test code | `orchestrator/tests/` | production対象外 |
| **単位5合計** |  | **98〜128** |

単位6に保守的に80行を残す場合、単位5の許容上限は146行なので、**s1/briefどおりの薄いwriterなら収まるが、余裕は18〜48行しかない**。

ただし、後述のD574準拠でapproval payload側のtrust edgeまで実装する場合は、少なくとも **125〜175行程度**となり、単位6の余地を保証できない。

## 1. §6.10の二箇条の判定

### 箇条1: writer認可

これは単位5の新規スコープ。

[`_binding.py:1-7`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_binding.py:1) は、snapshot照合は単位5のwriter入口の責務であり、本moduleはwriterを持たないと明記している。

[`_receipt_io.py:151-164`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_receipt_io.py:151) の `create_receipt_bytes` も、低位のcreate-only I/Oであり、将来のwriterがbinding比較を上乗せすると明記している。repo全体をgrepした結果、receipt writerの実装は存在せず、呼び出しは定義本体とunit2テストだけだった。

### 箇条2: pointer実在・size・sha256

これは実装済みで、単位5は再実装しない。

- [`_semantic_validator.py:312-370`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_semantic_validator.py:312): strict relative path、size、単一fd読取、sha256再計算。
- [`_semantic_validator.py:2285-2345`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_semantic_validator.py:2285): 全fileRecordを走査。
- [`_semantic_validator.py:666-703`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_semantic_validator.py:666): preregistration blobRefをcommit treeから再読。
- [`_safe_io.py:312-390`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_safe_io.py:312): `O_NOFOLLOW`、snapshot前後比較。
- [`_safe_io.py:398-530`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_safe_io.py:398): O_EXCL、全量write、fsync、atomic hard-link。
- [`_git.py:458-498`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_git.py:458): Git blobのsize・sha256検査。

したがって、箇条2の新規production行数は **0行**。

## 2. writer実装地図

新規private moduleを想定する。

```python
def _publish_receipt(
    *,
    repository_root: str | os.PathLike[str],
    relative_path: str,
    raw_bytes: bytes,
    binding: _PreregBinding,
) -> None:
    ...
```

予定フローは以下。

1. `type(raw_bytes) is bytes` を確認。
2. `binding.assert_intact(repository_root)` をpublish前に実行。
3. `parse_receipt_bytes(raw_bytes, label=relative_path)` でduplicate key等を検査。
4. `_receipt_schema._load_schema_from_ref(repository_root, binding.record.receipt_schema)` でbinding由来のschemaだけを読む。
5. `_semantic_validator._validate_receipt_semantics(...)` を呼ぶ。
6. 直前にもう一度 `binding.assert_intact()` を呼ぶ。
7. 既存の `create_receipt_bytes(...)` に元のbytesを渡して永続化する。

三つ組の照合はwriterで重複実装せず、既存validatorを呼ぶことで満たす。

- receiptの8-key `preregistration` と `binding.record` の `core`、`addendum_a/b`、`fold_commit`、`errata`、`approval_manifest`、`receipt_schema`、`composed_core_sha256`。
- `binding.prereg_commit` を注入した内部9-fieldとの完全一致。実装済み: [`_semantic_validator.py:594-663`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_semantic_validator.py:594)。
- `measurement_checkout.repository_head == binding.measurement_head`。実装済み: [`_semantic_validator.py:1241-1253`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_semantic_validator.py:1241)、呼出しは [`:2587-2591`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/_semantic_validator.py:2587)。

別経路writerの機械的制御は次で行う。

- `_writer.py` のみがproduction codeとして `create_receipt_bytes` を呼ぶ。
- unit5テストでASTを走査し、他のproduction moduleからのreceipt publish呼出しを拒否する。
- `submission_gate/__init__.py` の空の `__all__` を維持する。
- `publish_receipt`、`PreregBinding`、既存D264の4名前をtop-levelへ出さない。
- 新しいpublic dataclassは作らず、sealedな `_PreregBinding` を唯一のwriter capabilityとして受ける。

Pythonのprivate名はimportすれば触れるという限界はD563自身も認めているため、これはrepository内のproduction call graphとexport面による保証になる。

## 3. conformance vectors

vectorsはproduction moduleではなく、次のtest資材に置ける。

```text
orchestrator/tests/fixtures/t338_submission_gate/conformance/
  index-v1.json
  positive-v1.json
  negative-*.json
```

production validatorがvector indexをruntimeで読む必要はない。indexを読むのはunit5のconformance testだけなので、`submission_gate/*.py`の行数対象外にできる。

1ファイル1vectorを推奨する。`index-v1.json`には、sortedな以下を持たせる。

```text
{id, path, sha256, expected_reason, covers}
```

mutation記述は既存fixtureからfull receiptを作り、1条件だけ変更する形式にする。単位3のfixtureを再利用する。

- `_file_record`: [`test_t338_submission_gate_unit3.py:74-82`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/tests/test_t338_submission_gate_unit3.py:74)
- `_preregistration_value`: [`:89-111`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/tests/test_t338_submission_gate_unit3.py:89)
- `_make_git_fixture`: [`:153-298`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/tests/test_t338_submission_gate_unit3.py:153)
- `_full_receipt`: [`:301-613`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/tests/test_t338_submission_gate_unit3.py:301)

unit3には37個のtest functionがあり、代表的な正例は [`:631-638`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/tests/test_t338_submission_gate_unit3.py:631)、pointer負例は [`:923-935`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/tests/test_t338_submission_gate_unit3.py:923)、preregistration負例は [`:1024-1032`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/tests/test_t338_submission_gate_unit3.py:1024)にある。

ただし、部分Mappingを直接private helperへ渡す既存負例は、そのまま正式vectorとは呼ばない。shape gateを通るfull receiptへ昇格できるものだけをvector registryへ再ラベルし、それ以外は既存unit testとして残す。

vector数は基準文書間に差がある。

- s1分類のA級だけなら、正例1 + §6 A級35件 = **36件以上**。§7.1 A級18件は `covers` の重複で吸収する。
- `record-items-v2.md §7` の逐語を全41箇条に適用するなら、正例1 + 41負例 = **42件以上**。これはs1のB級見送り方針と衝突するため、author前に確定が必要。
- writer引数欠落などJSONに表せないものは、`kind="api"` のarchitecture vectorとしてunit5 test内で検査する。

## 4. manifest pinの設計

s1分類だけを採るなら、別型ではなく既存のsealed `ApprovedManifest`へ1 field追加する。

予定位置は以下。

```text
_manifest.py:147-149   conformance_vector_index_sha256: str
_manifest.py:151-170   keyword-only constructor、token検査、保存
_manifest.py:173-198   64桁hex検査、freeze
_manifest.py:216-226   loaderからの値供給
```

`approved_blobs`へroleを追加してはいけない。現行approval payloadはexact 6 roleで、[`approval_payload.py:461-498`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/preregistration/approval_payload.py:461) がrole集合を固定している。

しかし、現在のrepoにはvector digestの供給元がない。

- `ApprovedManifest`にvector fieldは未存在。
- `ApprovalPayload`のtop-level exact key [`:38-50`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/preregistration/approval_payload.py:38) にvector fieldはない。
- `ApprovalPayload` dataclass [`:144-155`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/preregistration/approval_payload.py:144) にもない。
- 現行のtest fixture・manifest vector資材も存在しない。

さらに、最新のD574はs1分類と異なり、manifest単独pinを否定している。

- [`docs/decisions.md:23166-23188`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/docs/decisions.md:23166) は、期待値をapproval payload側の `(path, commit, sha256)` 三つ組に置き、manifest宣言と照合するよう決定している。
- これに従うならfieldは単なるsha256ではなく `conformance_vector_index: BlobRef` になる。
- `approval_payload.py`のexact parserと凍結済みpayload bytesも変更対象になり、単位5の薄い1-field追加ではない。

## 5. consumer・波及

repo全体のgrepでは、現行 `submission_gate` の外部production consumerはなく、直接呼ぶのはunit1〜4 testだけだった。unit6までtop-level APIへ配線しない方針は維持する。

[`submission_gate/__init__.py:1-7`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-unit5/orchestrator/submission_gate/__init__.py:1) は空のimport surfaceであり、unit1もD264の4名前が非exportであることを検査している。

単位5から新規に呼ぶ必要があるものは次のとおり。

- `orchestrator/preregistration/blobref.py`: **新規直接呼出しなし**。D563どおりwrapper化せず、既存のsubmission_gate内部helperを経由する。
- `orchestrator/qualification/attempt_ledger.py`: **なし**。receipt writerはunit4のattempt authorityとは別責務。
- `orchestrator/campaign/trial_registry.py`: **なし**。単位3/4で必要だったGit/historyパターンを単位5から再利用する必要はない。

`_event_chain.append_event` と `_attempt_authority` のevent persistenceもreceipt writerではないため、receipt publish経路へ統合しない。

## 6. NO-GO判定

現時点の判定は **条件付きNO-GO**。

薄いwriter自体の設計と予算は成立するが、author開始には次を先に固定する必要がある。

1. s1分類の「manifest自己pin」を採るのか、より新しいD574の「approval payload側三つ組trust edge」を採るのか。
2. vector indexのcanonical path、commit、sha256の実値と供給元。
3. §6のvector範囲をA級35件に限定するのか、record-items逐語どおり全41件にするのか。
4. writerのreceipt destination namespace。現行safe I/Oは安全な相対pathを受けるだけで、receipt専用namespaceは未定義。
5. 指定された `output/insights/2026-08-20_t338-submission-gate-unit34/verbatim/s2-plan.md` は存在せず、同ディレクトリには `package.md` のみだった。

D574を採るなら、単位5単独では実装開始せず、approval payload／manifest／vector indexのauthorityを先に裁定するべきである。s1分類を明示的に優先する裁定が出れば、下記の薄いwriter案でauthorへ進める。

## 総括

(a) 予算判定: 現在 **5,974行、残余226行**。s1/brief準拠の単位5は **98〜128 production行**で、単位6へ80行を残しても名目上は収まる。ただし余裕は18〜48行で際どい。D574準拠のpayload-side trust edgeまで含める場合は **125〜175行以上**となり、単位6の余地を保証できない。

(b) 判定: **条件付きNO-GO**。writer本体とpointer再利用の設計はGOだが、vector pinのauthority、canonical payload、vector範囲、destination namespaceが未確定。

(c) production見積り範囲: **98〜128行（s1/brief準拠の薄い単位5）**。D574を含む完全なauthority変更は別途で、現時点では承認済み見積りにできない。

編集・pytestは実施していない。