# freeze 族の恒久設計 — 第 2 設計段パッケージ

**状態: 第 2 設計段パッケージ — 未了 = U-A1 (ユーザー裁定) + conformance 期待出力 literal の確定
(W-a 開始前 gate、決定権者 = W-a 実装 wave の親、手順 = §S2-2b.3)、親裁定 2026-07-22**

本書は、親裁定 2026-07-22 に基づき、第 1 設計段
`docs/freeze-permanent-design.md` §13 の残課題を実装可能な exact 仕様へ展開した設計文書である。
第 1 設計段 §2〜§10 の承認済み骨格・政策を変更しない。衝突時は第 1 設計段が上位であり、本書はその
具体化として読む。ただし、第 1 設計段が「exact 符号化は第 2 設計段」と委譲した placeholder は本書の
exact 仕様が置換する。特に第 1 設計段 §7-A の bundle digest は同節の訂正済み 7 component と本書
§S2-2 が同一契約である。

本書は段完了時に凍結する **design 族**であり、`tools/check_docs.py` の `LIVING_DOCS` には編入しない。
U-A1 裁定後、その裁定に依存する field/check/CLI/変異候補と、§S2-2b.3 の手順で確定した conformance
期待出力 literal だけを同一設計段の最終 patch として確定し、それ以後は実装都合で本文を書き換えない。
訂正が必要な場合は新しい設計段または明示 erratum を作る。

規範語「必須」「拒否」「のみ」は実装契約を表す。観測値は 2026-07-22 の
`HEAD=6a8f5524bfa82410937cc72a8393a76c0005e5d8` に対する実測であり、生成時確定値として明記したものを
schema literal にしてはならない。

---

## §S2-1 lineage / receipt / approval / pointer / revocation / cancellation

### S2-1.1 共通表現

- SHA-256 は JSON string、`^[0-9a-f]{64}$`。
- Git commit/blob OID は JSON string、`^[0-9a-f]{40}$`。実装開始時に
  `git rev-parse --show-object-format == sha1` を要求する。
- generation は `bool` でない JSON integer、`N >= 0`。
- UTC は `YYYY-MM-DDTHH:MM:SSZ` のみ。fraction、offset、date-only を拒否する。
- repo path は空でない POSIX 相対 path。先頭・末尾 `/`、`//`、`\`、`.` / `..` component、
  control character を拒否する。
- governance record は mode `100644` の Git blobのみ。symlink、gitlink、executable blobを拒否する。
- 全 string は Unicode NFC。U+0000〜U+001F、U+007F を拒否する。

governance record、§S2-1.5/§S2-2b.4 の tracked report、および **g1 以後の known / measurement /
holdout family artifact 本体**の canonical bytes は次で固定する。legacy g0 の3 artifactは歴史 bytesを
そのまま root とするため、この再符号化の対象外である。

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

raw bytes は canonical bytes と byte-for-byte 一致し、BOM・末尾改行を持たない。duplicate key、
NaN、Infinity、top-level 非 objectを拒否する。g1+ family artifact は parse 後の値を上記 encoder へ
戻した bytes が artifact raw bytes と一致しなければ、schema/semantic 値が同じでも拒否する。

実物根拠: `orchestrator/campaign/s8b_ratified_freeze.py` の canonical JSON、Git hardening、
`docs/freeze-permanent-design.md` §§4, 6。  
owner: canonical I/O は **W-a**、governance predicate は **W-c**。

### S2-1.2 family generation header

別の lineage JSON は作らない。lineage の正本は各 family artifact の共通 header、receipt、pointer である。

| field | exact 制約 | owner |
|---|---|---|
| `schema_version` | known=`s1-known-axes-freeze/v2`、measurement=`s1-measurement-freeze/v3`、holdout=`8b-holdout-freeze/v3` | W-b / W-c |
| `generation_number` | `N >= 1`。3 family と path の N が一致 | W-b / W-c |
| `supersedes_sha256` | g1 は対応 legacy raw SHA-256、N>1 は同 family g(N-1) raw SHA-256 | W-b / W-c |
| `provenance_unverified` | exact `{generator,python_version_at_generation,related_implementations}`。全体が M | W-b / W-c |
| `generator` | exact `{path,sha256_at_generation}` | W-b / W-c |
| `python_version_at_generation` | 非空 NFC string。gate の再構成入力に使用禁止 | W-b / W-c |
| `related_implementations` | `{path,sha256_at_generation}` の path 昇順・一意 array | W-b / W-c |

generation path は次だけである。

```text
output/s1-freeze/known_axes_freeze.v2.g<N>.json
output/s1-freeze/measurement_freeze.v3.g<N>.json
output/s8b-freeze/holdout_freeze.v3.g<N>.json
```

g1 の `supersedes_sha256` は次で固定する。

```text
known       354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516
measurement 203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a
holdout     315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688
```

実物根拠: legacy 3成果物と `orchestrator/tests/test_frozen_artifacts.py`。  
owner: **W-b / W-c**。

### S2-1.3 g1 transition receipt

path:

```text
output/freeze-migrations/legacy-to-permanent-g1.receipt.json
```

top-level は exact 10 fields、全て必須。

```text
schema_version
transition_id
generation_number
generation_commit
h_gen
legacy_inventory
successors
projections
holdout_confirmation
observation_audit_input
```

| field | exact 制約 |
|---|---|
| `schema_version` | `freeze-family-transition-receipt/v1` |
| `transition_id` | `legacy-to-permanent-g1` |
| `generation_number` | `1` |
| `generation_commit` | 3 artifact を追加した G |
| `h_gen` | `G^`。G の唯一 parent |
| `legacy_inventory` | exact 9 elements |
| `successors` | exact 3 elements、known/measurement/holdout 順 |
| `projections` | exact 3 elements、同じ family 順 |
| `holdout_confirmation` | S2-1.6 の exact object |
| `observation_audit_input` | S2-1.7 の exact object。結果/statusを持たない |

`legacy_inventory[*]` は exact 8 fields。

```text
family
emission_commit
path
git_blob_oid
raw_sha256
recorded_frozen_at_head
anchor_status
disposition
```

配列値は次で固定する。

| # | family | emission commit | blob OID | raw SHA-256 | recorded anchor |
|---:|---|---|---|---|---|
| 1 | known | `80b30107ea17397c0881818c54c12856d5e77dcb` | `701cd39ebeeb0e115e0772c91a00637a6b2d994c` | `1622ecadde1cf8fd432c804d198ded8f0b3ce89b19d02503c6b77fee86952cdd` | `c648bbe2aa8dff028411b3b53a3ba8e6767bdb15` |
| 2 | known | `15fcc08fb78d6067f21aaf564c03d60ec36de649` | `b31927be81e24d6801af6303cdf119ecbd37ea6f` | `e1b0a5348034b5bf6e938ff498802ccc2d43cd2b646ed745c5f3d803ca05fd8e` | `ca921338507ad66540ceae997b327e6c3ab3cb3d` |
| 3 | known | `8f7fca22043dff8002e11ae9f03b5cc60e71e428` | `90d987722021bc1d01daa10b0cdb6f0d541fcdc0` | `7a7458df4ee4350ff500f7b47662fe74ae8e3d0936430c1dda8c3a8fcb012f3e` | `c890e958acfc3e2456e0033648069a9f2f297b81` |
| 4 | known | `b4e5cb621e3f8f93de952e9400d4b8dcd34107e0` | `47fa327efe555d9113119daafc79706838b8ec9a` | `3eb808b4b751d5dc57e57e214fc6d7fea9a9c702a0208b5f0e87f094ae65bce1` | `0f304270954eacd6df136bbac50da649e289833d` |
| 5 | known | `e5dfa84c6e71824e2312af99b97d60dde11eca20` | `18346a35a00a71f8986f47d54afc1a2392fbfb27` | `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` | `2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1` |
| 6 | measurement | `4b9d86e3c50b9c48748e8935217d8a2ac500d74d` | `fd2bc0e52479cc1e352f172a99b2476d6355b507` | `09dd1585ca28aebfbae0e724e4bacb299452dbad1b21eb67e893795d999756f6` | `02c840c4a001f8df6810355471806cb251400fdf` |
| 7 | measurement | `b4e5cb621e3f8f93de952e9400d4b8dcd34107e0` | `8c15edcd9ff0d10b00145e2a137dd4cbeb92e69a` | `5c719c076e17f385a781933c081bf02abcd85b9edb01ad8c50a37740c134a191` | `0f304270954eacd6df136bbac50da649e289833d` |
| 8 | measurement | `e5dfa84c6e71824e2312af99b97d60dde11eca20` | `edfe2ed71b80b8aa44dabd2a7d669c4dcde18d26` | `203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a` | `2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1` |
| 9 | holdout | `911f6bc0407c6a6479b0edcb3d0c0b95ab1730e2` | `3803df1f63c84c3c9bf79e590b8a5b4a4943e02c` | `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` | `2e20d441aaf7ae267e941ecda09e4b53050943cf` |

全要素で `anchor_status=="missing"`、`disposition=="legacy-history-only"`。
path は family ごとに legacy 3 path。唯一 key は `(family,emission_commit,path)`。

`successors[*]` は exact 7 fields。

```text
family
path
schema_version
generation_number
raw_sha256
git_blob_oid
supersedes_sha256
```

`projections[*]` は exact 4 fields。

| family | `contract_id` | `removed_claims` | `metadata_sources` |
|---|---|---|---|
| known | `known-legacy-to-v2/v1` | `["/frozen_at_head"]` | `["/generator","/python_version"]` |
| measurement | `measurement-legacy-to-v3/v1` | `["/frozen_at_head"]` | `["/generator","/python_version","/implementation_hashes/s1_measurement_freeze","/implementation_hashes/s1_stats"]` |
| holdout | `holdout-legacy-to-v3/v1` | `["/frozen_at_head"]` | `["/generator"]` |

`metadata_sources` の意味は「旧 G から除去した pointer の列挙」だけである。M の値を projection predicate、
再構成入力、pass 判定に使用してはならない。

実物根拠: legacy 9 blob、旧3 artifact、`docs/freeze-permanent-design.md` §§1, 6, 8。  
owner: schema/verifier **W-c**、known/measurement projection **W-b**、実 record 発行 **W-e**。

### S2-1.4 gN→gN+1 receipt

N≥2 の path:

```text
output/freeze-migrations/permanent-g<N-1>-to-g<N>.receipt.json
```

top-level exact 9 fields:

```text
schema_version
transition_id
generation_number
generation_commit
h_gen
predecessors
successors
holdout_confirmation
observation_audit_input
```

- `schema_version=="freeze-family-generation-receipt/v1"`
- `transition_id=="permanent-g<N-1>-to-g<N>"`
- `generation_number==N`
- `predecessors` は family 順の exact 3 elements。各要素は
  `{family,path,generation_number,raw_sha256}`。
- `successors`、confirmation、audit input は g1 と同じ型。

transition receipt は現行 `s8b_ratified_freeze.py` に存在しない完全新設 schema である。

owner: **W-c**、実 record 発行 **W-e または将来の generation wave**。

### S2-1.5 generation search report

holdout confirmation が束縛する generation search report は content-addressed tracked artifact である。

```text
output/freeze-permanent/reports/generation-search-<raw_sha256>.json
```

本文は canonical JSON の exact 8 fields。

```text
schema_version
validation_head
generation_number
h_gen
enumerated_paths_sha256
exemptions
holdouts
positive_control
```

- `schema_version=="freeze-holdout-generation-search-report/v1"`
- `validation_head` は40hex commitで `h_gen` と一致する。search はこの単一 tree に対して行う。
- `enumerated_paths_sha256` は検索対象 path array の canonical bytes SHA-256。
- `exemptions` は `{path,sha256}` の path 昇順 array。
- `holdouts` は `rr80`,`rr20` 順。各要素は exact
  `{candidate_id,expressions,per_axis_counts,conjunction_hits,result_sha256}`。
- generation search では両 `conjunction_hits` が空でなければ G を作らない。
- `positive_control` は exact
  `{fixture_key,fixture_path,fixture_sha256,expected_hit_paths,actual_hit_paths}`。
- report 自体は receipt へ埋め込まず、その canonical raw bytes SHA-256 を confirmation が束縛する。
- filename の `<raw_sha256>`、raw bytes SHA-256、confirmation の `search_report_sha256` は全一致する。
- report bytesはgeneration live searchと同時にtransaction directoryへO_EXCL保存し、holdout stageが
  参照した同一bytesを§S2-1.14のQでtracked treeへ導入する。Q/resolverはcanonical schema、path/raw hash、
  generation/h_gen、active exemptionとの一致、両holdoutのempty hit、positive-controlのexpected/actual一致を
  再検査する。root untracked memberはH_gen treeから再構築できないため、enumerated path集合の完全再導出を
  主張しない。この残余は§S2-12.1に明示する。任意の64hexだけをconfirmationへ記録する実装は禁止する。

owner: schema/rebuild predicate **W-c**、tracked record発行 **W-e**。

### S2-1.6 holdout confirmation

exact 4 fields:

```json
{
  "confirmed_by": "<non-empty NFC string>",
  "confirmed_at": "<UTC seconds>",
  "holdout_sha256": "<64hex>",
  "search_report_sha256": "<64hex>"
}
```

- successor holdout の `confirmed_by` / `confirmed_at` と一致する。
- `holdout_sha256` は successor raw hash。
- `search_report_sha256` は S2-1.5 の同 generation tracked reportの raw SHA-256。導出pathの実在、
  filename/raw hash、canonical本文、`validation_head==h_gen` の全てを検査する。
- 各 generation で再発行する。前 generation の pair/hash のコピーを拒否する。
- `confirmed_at` は前 generation より後でなければならない。
- 同一人物による再確認を許すため、`confirmed_by` の文字列自体は前 generation と同値でもよい。
- approval approver と confirmation confirmer は同一人物である必要はない。

owner: **W-c**。

### S2-1.7 observation audit input

receipt の `observation_audit_input` は exact 5 fields。

```text
schema_version
h_gen
measurement_sha256
wal_sources
observation_count
```

- `schema_version=="s1-observation-audit-input/v1"`
- `h_gen` は receipt top-level と一致。
- `measurement_sha256` は successor measurement hash。
- `wal_sources` は floor/block1/block2 順の exact 3 elements。
- 各 element は exact
  `{wal_source_id,wal_path,wal_blob_oid,wal_sha256,record_count}`。
- `observation_count` と `record_count` は生成時に実 blobから確定する。
- `status`、`verified`、`passed`、reason、report hashを置かない。

R が束縛するのは audit 入力だけである。A 作成時に同じ入力から WAL audit を再実行し、その report hash を
approval に含める。

owner: **W-b** predicate、Git tree reader **W-a**、receipt integration **W-c**。

### S2-1.8 approval record

path:

```text
output/freeze-permanent/approvals/<approval_raw_sha256>.json
```

U-A1 非依存部分は exact 8 fields。

```text
schema_version
generation_number
bundle_digest
components
reports
approver
approved_at
scope
```

| field | exact 制約 |
|---|---|
| `schema_version` | `freeze-bundle-approval/v1` |
| `generation_number` | N≥1 |
| `bundle_digest` | §S2-2 の再計算値 |
| `components` | exact 7 elements、§S2-2 の固定順 |
| `reports` | exact `{verification_sha256,projection_sha256,wal_audit_sha256}` |
| `approver` | 1〜128 code points、NFC、trim 済み |
| `approved_at` | UTC seconds |
| `scope` | `freeze-bundle-digest+verification-report+projection-report+wal-audit-report/v1` |

`components[*]` は exact `{kind,sha256}`。indices 4〜6 は `reports` の3値と一致する。
filename は approval canonical raw bytes の SHA-256 と一致する。

`reports` の各値から次の tracked pathを一意に導出する。

```text
verification_sha256 -> output/freeze-permanent/reports/verification-<hash>.json
projection_sha256   -> output/freeze-permanent/reports/projection-<hash>.json
wal_audit_sha256    -> output/freeze-permanent/reports/wal-audit-<hash>.json
```

U-A1 が選択する expiry field と意味は §S2-11 に隔離する。裁定前に field 名、field count、clock predicate、
CLI argvを確定した扱いにしてはならない。

A 作成 CLI は次を、Qに記録された `validation_head` treeと同一入力から再実行する。

1. registered-inactive bundle verification
2. legacy→g1 または gN transition projection
3. WAL observation audit

各再実行結果の canonical bytes がQの tracked report bytesと一致し、aggregate が `pass` の場合だけ
approval bytes を作る。approval record に report status の自己申告を置かず、actual result 列から得た
report SHA-256 のみを承認対象とする。

resolver と A 作成 CLI は3 reportを個別に、少なくとも次の順で毎回再検査する。

1. 導出pathが `H_v` / A入力treeに mode `100644` のblobとして実在する。
2. raw bytes SHA-256が approval field および filenameのhashと一致し、§S2-1.1のcanonical bytesである。
3. 本文 `subjects` の known / measurement / holdout / receipt 4 hashが解決中bundleと固定順で一致する。
4. `results` から再導出した `aggregate` が literal `pass` である。
5. 40hex `validation_head` が存在し、Qの唯一parentと一致し、`H_v` から到達可能である。

3 report hash field の存在、string 型、64 lowercase hex、componentsとの一致もこれらに先行して検査する。
report hashを欠落・未知 fieldとして捨てるfallback、任意64hexだけでreport確認済みとする実装は禁止する。

owner: report/approval predicate **W-c**、Q/A record作成・commitは **W-e** (Aは人間承認者)。

### S2-1.9 active-bundle pointer

path:

```text
output/freeze-permanent/active/<pointer_raw_sha256>.json
```

top-level exact 7 fields。

```text
schema_version
generation_number
parent_active_sha256
bundle_digest
approval_sha256
artifacts
receipt
```

artifact は family 順の exact 3 elements、各 exact
`{family,path,schema_version,generation_number,sha256}`。
permanent receipt は `{path,sha256}`、g0 では null。

g0 canonical raw bytes は次で固定する。

```json
{"approval_sha256":null,"artifacts":[{"family":"known","generation_number":0,"path":"output/s1-freeze/known_axes_freeze.json","schema_version":null,"sha256":"354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516"},{"family":"measurement","generation_number":0,"path":"output/s1-freeze/measurement_freeze.json","schema_version":null,"sha256":"203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a"},{"family":"holdout","generation_number":0,"path":"output/s8b-freeze/holdout_freeze.json","schema_version":"8b-holdout-freeze/v1","sha256":"315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688"}],"bundle_digest":null,"generation_number":0,"parent_active_sha256":null,"receipt":null,"schema_version":"freeze-active-bundle-pointer/v1"}
```

raw SHA-256 と path:

```text
746fcafabaaef09f11bc945dafc63eb177c94df5c1fb2735aadb230be2260e4b
output/freeze-permanent/active/746fcafabaaef09f11bc945dafc63eb177c94df5c1fb2735aadb230be2260e4b.json
```

g0 は唯一の `parent_active_sha256=null` pointer。第二 genesis を拒否する。

resolver は開始時に `H_v` を一度捕捉し、同じ tree から governance 全件、pointer chain、tip の3 artifact、
receipt、approvalを一度だけ読む。family 別の再 resolve を禁止する。

pointer chain は `g0 → g1 → … → gN`。child generation は parent+1、parent hash、3 family、
receipt、approval、bundle digestを全一致させる。「最大 N」「最新 commit」「最新 approval」による選択を
禁止する。revoked/cancelled/invalid tip から旧 generation へ fallback しない。

返却型:

```text
ActiveOfficialLegacyBundle  # g0 adapter 3件を含む
ActiveOfficialBundle        # g1+、3 family lockstep
```

owner: resolver/schema **W-c**、consumer cutover **W-d**、g1 X **W-f**。

### S2-1.10 revocation

path:

```text
output/freeze-permanent/revocations/<bundle_digest>.json
```

exact 7 fields:

```text
schema_version = "freeze-bundle-revocation/v1"
bundle_digest
approval_sha256
revoked_by
revoked_at
scope = "bundle-only"
reason
```

- bundle あたり0または1件。
- target は一度 X された N≥1 bundle。
- live tip の revocation 後は active bundleなし。fallback禁止。
- descendant generation は自動 revocation しない。
- record の変更・削除・rename・再追加を拒否。

owner: **W-c**、実行主体は人間。

### S2-1.11 fork cancellation

path:

```text
output/freeze-permanent/active-cancellations/<pointer_sha256>.json
```

exact 6 fields:

```text
schema_version = "freeze-pointer-cancellation/v1"
pointer_sha256
cancelled_by
cancelled_at
scope = "fork-loser-only"
reason
```

有効条件:

- target は g0 でなく、child を持たない leaf pointer。
- CX の唯一parent tree (`CX^`) で、同じ `parent_active_sha256` を持つ uncancelled child pointer集合を
  再構築し、その集合が exact `{target, selected_survivor}` の2件である。両者は同じgenerationのleaf。
- `CX^` と CX は target introduction **および selected survivor introduction の双方の後裔**である。
  どちらか一方しか履歴に含まないbranch上の先行cancellationを拒否する。
- cancellation 適用後の surviving child が `selected_survivor` ちょうど1件。
- target introduction が survivor introduction の祖先なら取消を拒否する。
- 唯一の live tip、generation を下げる取消、g0取消を拒否する。
- record の変更・削除・rename・再追加を拒否する。
- CX後に同parentの別siblingが導入された場合、そのsiblingはCX時点のfork集合に含まれないためCXで
  取消済みとは扱わず、通常のfork/unique-tip検査で拒否する。

owner: **W-c**、実行主体は人間。

### S2-1.12 generation transition allowlist

比較対象は `provenance_unverified` を除いた G projection。許可された field も target generation の
schema/semantic verifierと再導出一致を通らなければならない。

known gN→gN+1:

- 常時許可: `/generation_number`, `/supersedes_sha256`。
- `/entries/*/*/sources` の各配列は target `H_gen` と legacy projectionから再導出した配列全体と
  byte-for-byte同じJSON値である場合だけ配列全体を置換できる。個々の `path` / `sha256` / `lines` を
  独立allowlist leafとして扱わない。
- `/source_closure/records` は、§S2-7の型別規則で target `H_gen` から再導出した **exact union全体**と
  一致する場合だけ配列全体を置換できる。要素はpath UTF-8 bytes昇順、path一意、各要素 exact
  `{record_type,path,sha256,key}`。追加・削除・`record_type` / `key` / hash変更の一部だけを任意許可する
  実装を禁止する。
- `/source_closure/file_enumerations` も8 ID固定順の配列全体を再導出し、各 `members`、disposition、
  `file_count` を含む完全一致の場合だけ置換できる。path/member/countを前generationと同値に固定して
  `H_gen` の新集合を隠すことも、任意値へ変えることも拒否する。
- 上記3配列に差分がないgenerationでは同値のまま保持する。差分がある場合は一部leaf更新でなく、
  target `H_gen` からの再導出結果への全体置換だけを正当なgeneration diffとする。
- selection rules、entry key、選定値、flags、pairing、`ccbench_pin` は不変。
- Gの3 artifact追加以外のdiffと、このallowlistに無いsemantic diffは
  `lineage.generation-diff` で拒否する。

measurement gN→gN+1 の許可面:

```text
/generation_number
/supersedes_sha256
/known_axes_freeze/path
/known_axes_freeze/sha256
/cells
/s1b_pairing
/observations
/analysis_results
```

known 2 leaf は同じ bundle の known generation と lockstep。cells/pairing は known から再構成する。
comparisons 12件、operating point、workload flags、master seed、schedule、ccbench pin は不変。

holdout gN→gN+1 の許可面:

```text
/generation_number
/supersedes_sha256
/known_axes_freeze/path
/known_axes_freeze/sha256
/holdouts/rr80/variant_binding
/holdouts/rr20/variant_binding
/search
/positive_control
/confirmed_by
/confirmed_at
/lifecycle_stage
/env_tag
/floor
/budget
/floor_protocol
/floor_source
/measurement_closure
/refreeze_note
```

- known path/hash と variant binding は同 bundle の known から再導出する。
- confirmation は S2-1.5/1.6 に従い generation ごとに fresh。
- `lifecycle_stage` は同値または `pre-measurement → ratified-floor` のみ。
- `env_tag` は `null → registry 登録済み string` を一度だけ許可。
- search/positive-control は当該 generation の search reportとの再導出一致を要求する。
- holdout axis、derangement、design source、match convention は同 lineage 内で不変。

known source の current worktree drift を static verify の拒否理由にしないこと、および commit identity から
内容同値へ交換することは受理集合を広げる。§S2-12 の §14 追記案を交換条件とする。

owner: known/measurement **W-b**、holdout/lineage **W-c**。

### S2-1.13 件数・一意性

- generation N があれば1..Nの各 generationに3 familyと1 receiptが存在する。
- 同一 `(family,N)` path は Git historyで追加1回だけ。
- 3 artifact は同じ G で導入する。
- receipt は generation あたり1件。
- approval は bundle あたり0件以上。pointerが参照する approval は1件。
- uncancelled child pointer は parent/generationごとに1件。
- revocation は bundle あたり0/1、cancellation は pointer あたり0/1。
- generation rollback、gap、family混在を拒否する。
- dedicated namespace の未知 fileを無視せず拒否する。
- `H_v` reachable historyで各 governance/generation recordの導入後 M/D/R/C/T を拒否する。

### S2-1.14 commit topology

```text
H_gen <- G <- R <- L_prod <- L_manifest <- Q <- A <- X
```

| commit | parent / ancestry | exact diff | merge | authorization |
|---|---|---|---|---|
| G | parent exactly H_gen | generation N の3 artifactを `A` で追加 | 禁止 | project provenance |
| R | parent exactly G | generation N receipt 1件を `A` で追加 | 禁止 | project provenance |
| L_prod | parent exactly R | `freeze_permanent_roots_g<N>.py` 1件を `A` で追加 | 禁止 | project provenance |
| L_manifest | parent exactly L_prod | `test_frozen_artifacts.py` 1件を `M` | 禁止 | project provenance |
| Q | parent exactly L_manifest | generation-search / verification / projection / wal-audit の content-addressed report 4件を `A` | 禁止 | project provenance |
| A | parent exactly Q | approval 1件を `A` | 禁止 | raw/parsedとも `AI-Agent: none` |
| X | parent exactly selected A | pointer 1件を `A` | 禁止 | raw/parsedとも `AI-Agent: none` |
| RV | target X の後裔 | revocation 1件を `A` | 禁止 | raw/parsedとも `AI-Agent: none` |
| CX | target と selected survivor の両 introduction の後裔 | cancellation 1件を `A` | 禁止 | raw/parsedとも `AI-Agent: none` |

g0 pointer introduction `P0` は W-c で1 record追加のみ、非 merge、project provenanceとし、以後 immutable。

G/R/L_prod/L_manifest/Q/A/X は pairwise非同一。`diff-tree --no-renames --name-status -r` の exact setを使う。
Qの4 pathは§S2-1.5/§S2-2b.4からraw hashで一意導出し、各reportの `validation_head==Q^`
(generation-searchだけは `validation_head==h_gen`) を要求する。RV/CXにもA/Xと同じ単一record追加・
非merge・人間trailer制約を課す。

実物根拠: 現行 approval/pointer/revocation/cancellation parser と immutable introduction は
`orchestrator/campaign/s8b_ratified_freeze.py`。transition receipt は新設。  
owner: verifier/CLI **W-c**、literal更新 **W-e**、X **W-f**。

---

## §S2-2 bundle digest の exact 符号化

入力は次の raw SHA-256 7件、固定順である。

```text
0 known
1 measurement
2 holdout
3 receipt
4 verification_report
5 projection_report
6 wal_audit_report
```

canonical payload:

```json
["<known64>","<measurement64>","<holdout64>","<receipt64>","<verification64>","<projection64>","<wal-audit64>"]
```

```python
payload = json.dumps(
    components,
    ensure_ascii=False,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")

DOMAIN = b"izanagi.freeze-family.bundle-digest/v1\x00"
bundle_digest = hashlib.sha256(DOMAIN + payload).hexdigest()
```

array lengthは7。各要素は lowercase 64hex。空白、BOM、末尾改行なし。domainのNULを削除・変更してはならない。

次を全一致させる。

```text
recomputed digest
approval.bundle_digest
pointer.bundle_digest
approval.components の再計算値
approval.reports と components[4:7]
```

component順序とdomain separatorは別 predicate・別変異点とする。

実物根拠: 第1設計段 §7-A の7-component契約 (起草時4-componentを親裁定 J1 とレビュー R1-1 で訂正済み)。本節と同一契約。  
owner: encoding **W-a**、governance integration **W-c**。

---

## §S2-2b observations / analysis_results

### S2-2b.1 observations

measurement v3 `/observations` は exact 6 keys。

| field | exact 制約 |
|---|---|
| `schema_version` | `s1-measurement-observations/v1` |
| `unit` | `transactions_per_second` |
| `value_encoding` | `python-float.hex/binary64` |
| `rounding` | `source-json-to-binary64-roundTiesToEven;no-decimal-rounding` |
| `wal_sources` | exact 3 elements |
| `records` | scheduleから再導出。現行設計では288件 |

288は18 cells × (floor 8 + block1 4 + block2 4)。件数を生成物から独立した自己申告として受理しない。

`wal_sources` の順序:

| index | id | schedule | role |
|---:|---|---|---|
| 0 | `floor` | `floor` | `floor` |
| 1 | `block1` | `test_block_1` | `block1` |
| 2 | `block2` | `test_block_2` | `block2` |

各要素は exact 8 fields。

```text
wal_source_id
schedule_name
campaign_role
wal_path
wal_blob_oid
wal_sha256
env_tag
campaign_start
```

`WalRecordLocator` は exact `{record_ordinal,raw_record_sha256}`。ordinalは1-based。
raw record hashは末尾1 byte LFを除いたrecord bytesのSHA-256。WAL全recordがLF終端でなければ拒否する。

現行 g1 候補の観測値:

| source | path | blob OID | raw SHA-256 | records |
|---|---|---|---|---:|
| floor | `output/campaigns/s1-direct-floor-direct-comparison-b82b9229/runs/wal.jsonl` | `07bde4386bc9a0acae3e8f22921d4c7de91b68c8` | `a5542d6cba6b4470a828e96e77f826dcd553ce38fe635a7a4c88141c03d99c38` | 1009 |
| block1 | `output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2/runs/wal.jsonl` | `63b7b8ec8f8c10caade711a533a2a01870f590ef` | `57726aadb08b1833cd2a8e919c9f766ac83c1cdce551c4bc82ad4fdeb1f2ad20` | 505 |
| block2 | `output/campaigns/s1-direct-block2-direct-comparison-9645b16a/runs/wal.jsonl` | `3d5f1b172727934c42a9290b4626ff12d9417d40` | `2194ca8936bb0d6f812e6ad94ffbd1f278ab40386abc5123c36d0ea75c7342bd` | 505 |

これらは2026-07-22のprojection値で、将来generationのschema literalではない。

`records[*]` は exact 8 fields。

```text
observation_id
schedule_name
lap
position
schedule_index
cell_id
value_tps_hex
source
```

`source` は exact 8 fields。

```text
wal_source_id
attempt
variant
session_start
value_record
session_result
value_json_pointer
value_origin_sha256
```

- `observation_id == schedule_name + ":" + schedule_indexの3桁zero-pad`
- `schedule_index==(lap-1)*18+position`
- records順は floor/block1/block2、各lap-major/position-minor。
- `value_json_pointer=="/payload/fitness_tps"`。
- `value_tps_hex` は正・有限で `float.fromhex(h).hex()==h`。
- `(schedule_name,schedule_index)`、observation_id、
  `(wal_source_id,value_record.record_ordinal)` はそれぞれ一意。

session区間は次で exact に定める。

1. `session_start` から identity tupleが一致する `session_result` までを閉区間とする。
2. 対応resultより前に次のsession-startが現れた場合は拒否する。
3. 区間同士の重複・入れ子を拒否する。
4. 区間内の `stage=="commit"` value recordはちょうど1件。
5. wrapperの exact vectorは次である。

```text
session_start  = (env_tag, source.variant, "s1-session")
value_record   = (env_tag, source.variant, "commit")
session_result = (env_tag, source.variant, "s1-session")
```

payload側の variant/attempt/campaign_role/lap/cell_id/schedule_indexも完全一致させる。

`value_origin_sha256`:

```text
SHA256(
  b"izanagi.freeze-observation-origin/v1\0"
  || bytes.fromhex(wal_source.wal_sha256)
  || uint64_be(value_record.record_ordinal)
  || bytes.fromhex(value_record.raw_record_sha256)
  || b"\0/payload/fitness_tps\0"
  || value_tps_hex.encode("ascii")
)
```

実物根拠: `orchestrator/campaign/wal.py`、現行3 WAL、measurement の18 cells/12 comparisons。  
owner: **W-b**。

### S2-2b.2 analysis_results

`/analysis_results` は exact 5 keys。

```text
schema_version = "s1-measurement-analysis/v1"
n_permutations = 4900
reference_alpha = {"numerator":1,"denominator":80}
comparisons
families
```

comparisons は measurement `/comparisons` と同じ順の12件。各要素は exact 9 fields。

```text
comparison_id
statistic_rank_sum_x2
p_permutation
gates
p_star
reference_below_alpha
judgment
effect_sizes
alternative
```

- `statistic_rank_sum_x2`: integer 40..104。
- `p_permutation` / `p_star` は exact `{numerator,denominator}`。両fieldともnon-bool integer、
  `1 <= numerator <= 4900`、`denominator==4900`。
- `alternative=="greater"`。
- 両gate passなら `p_star=p_permutation`、それ以外は `4900/4900`。
- `reference_below_alpha` は boolで `p_star.numerator*80 <= 4900` と同値。
- `judgment` は `established|not_established` で、上記boolと一対一。

`gates` は exact 2 keys。子objectまで次のkey-set・型で固定する。

```json
{
  "relative_median": {
    "passed": true,
    "relative_difference_hex": "<canonical-finite-hex>",
    "floor_left_cv_hex": "<canonical-finite-hex>",
    "floor_right_cv_hex": "<canonical-finite-hex>",
    "required_strictly_greater_than_hex": "<canonical-finite-hex>"
  },
  "direction_consistency": {
    "passed": true,
    "pooled_sign": 1,
    "stratum_signs": [1, 1]
  }
}
```

- `relative_median` は上記exact 5 keys。4つのhexはcanonical finite `float.hex()` stringでnull不可。
  thresholdは `max(floor_left_cv,floor_right_cv,0.03)`、`passed` は
  `relative_difference > threshold` の厳密不等号と同値。floor CVは各cellのfloor 8観測だけから得る。
- `direction_consistency` はexact 3 keys。`passed` はbool、`pooled_sign` は`-1|0|1`、
  `stratum_signs` はblock1/block2順のexact 2 integer (`-1|0|1`)。判定は次と同値。

```text
pooled_sign != 0
and stratum_signs == [pooled_sign, pooled_sign]
```

`effect_sizes` は exact 5 fields。

```text
median_difference
probability_superiority_stratified
probability_superiority_pooled
target_cv
control_cv
```

全floatは canonical `float.hex()` string。CVのみ型としてnullを持てるが、正の8観測から独立計算が非nullを
返す場合のnullを拒否する。

各stratumでtarget 4/control 4を結合し、average rankの2倍整数を使う。
`C(8,4)^2=4900` 全割付を列挙し、greater tailは `T >= T_obs`。
`families` はarrayで、順に`S-1a`、`S-1b`のexact 2 elements。各要素はexact 6 keys。

```text
family
method
comparison_ids
p_family
reference_below_alpha
judgment
```

- `method=="intersection-union/max-p-star"`。
- `comparison_ids` はmeasurement `/comparisons`順を保ち、S-1aは対応9件、S-1bは対応3件。
- `p_family` はexact rationalで denominator=4900、numeratorはmember `p_star.numerator` のmax。
- `reference_below_alpha` はboolで `p_family.numerator*80 <= 4900` と同値、`judgment` は
  `established|not_established` とboolの一対一。Holmではない。

浮動演算:

- 入力hexをbinary64へ一度復号。
- meanは正確な有理和/nを一度丸める。
- sample standard deviationは正確な有理式 `Σ(x-mean_exact)^2/(n-1)` の平方根を一度丸める。
- CVは **丸め済み standard deviation / 丸め済み mean** をbinary64除算し、その除算結果を
  round-to-nearest, ties-to-evenで一度丸める。十進中間値や未丸めmeanを使わない。
- even medianは加算丸め後に2除算を丸める。
- superiorityは整数勝/tie数から最終値だけ丸める。
- 十進桁丸めを禁止する。

producer `s1_measurement_freeze_v3.py` は既存 production `s1_stats` 系を使ってよい。
verifier `freeze_permanent_stats.py` は production moduleをimportしてはならない。逆方向importも禁止し、
AST/import graph testで機械検査する。

実物根拠: `orchestrator/campaign/s1_stats.py`、`s1_report.py`、`test_s1_stats.py`。  
owner: producer **W-b**、独立 verifier **W-a**。

### S2-2b.3 conformance vector input

次の入力bytesを本書で固定する。期待出力literalは§S2-11の許可holeである。

```json
{"id":"complete-separation","operation":"stratified-test","target":[["0x1.4000000000000p+2","0x1.8000000000000p+2","0x1.c000000000000p+2","0x1.0000000000000p+3"],["0x1.e000000000000p+3","0x1.0000000000000p+4","0x1.1000000000000p+4","0x1.2000000000000p+4"]],"control":[["0x1.0000000000000p+0","0x1.0000000000000p+1","0x1.8000000000000p+1","0x1.0000000000000p+2"],["0x1.6000000000000p+3","0x1.8000000000000p+3","0x1.a000000000000p+3","0x1.c000000000000p+3"]],"alternative":"greater"}
{"id":"partial-ties","operation":"stratified-test","target":[["0x1.0000000000000p+1","0x1.0000000000000p+1","0x1.4000000000000p+2","0x1.c000000000000p+2"],["0x1.4000000000000p+3","0x1.8000000000000p+3","0x1.8000000000000p+3","0x1.e000000000000p+3"]],"control":[["0x1.0000000000000p+0","0x1.0000000000000p+1","0x1.0000000000000p+2","0x1.8000000000000p+2"],["0x1.2000000000000p+3","0x1.8000000000000p+3","0x1.a000000000000p+3","0x1.c000000000000p+3"]],"alternative":"greater"}
{"id":"all-ties","operation":"stratified-test","target":[["0x1.c000000000000p+2","0x1.c000000000000p+2","0x1.c000000000000p+2","0x1.c000000000000p+2"],["0x1.c000000000000p+2","0x1.c000000000000p+2","0x1.c000000000000p+2","0x1.c000000000000p+2"]],"control":[["0x1.c000000000000p+2","0x1.c000000000000p+2","0x1.c000000000000p+2","0x1.c000000000000p+2"],["0x1.c000000000000p+2","0x1.c000000000000p+2","0x1.c000000000000p+2","0x1.c000000000000p+2"]],"alternative":"greater"}
{"id":"crossing","operation":"stratified-test","target":[["0x1.8000000000000p+1","0x1.8000000000000p+2","0x1.c000000000000p+2","0x1.0000000000000p+3"],["0x1.6000000000000p+3","0x1.8000000000000p+3","0x1.1000000000000p+4","0x1.2000000000000p+4"]],"control":[["0x1.0000000000000p+0","0x1.0000000000000p+1","0x1.0000000000000p+2","0x1.4000000000000p+2"],["0x1.a000000000000p+3","0x1.c000000000000p+3","0x1.e000000000000p+3","0x1.0000000000000p+4"]],"alternative":"greater"}
{"id":"strict-gate-equality","operation":"relative-gate","relative_difference_hex":"0x1.eb851eb851eb8p-6","floor_left_cv_hex":"0x1.eb851eb851eb8p-6","floor_right_cv_hex":"0x1.0000000000000p-6","fixed_min_hex":"0x1.eb851eb851eb8p-6"}
{"id":"direction-conflict","operation":"direction-gate","pooled_sign":1,"stratum_signs":[1,-1]}
{"id":"family-max","operation":"family-max","denominator":4900,"numerators":[1,62,3]}
{"id":"wrong-shape","operation":"stratified-test","target":[["0x1.0p+0","0x1.0p+1","0x1.8p+1"],["0x1.0p+2","0x1.4p+2","0x1.8p+2","0x1.cp+2"]],"control":[["0x1.0p+0","0x1.0p+1","0x1.8p+1","0x1.0p+2"],["0x1.4p+2","0x1.8p+2","0x1.cp+2","0x1.0p+3"]],"alternative":"greater"}
{"id":"nonfinite-token","operation":"stratified-test","target":[["nan","0x1.0p+1","0x1.8p+1","0x1.0p+2"],["0x1.4p+2","0x1.8p+2","0x1.cp+2","0x1.0p+3"]],"control":[["0x1.0p+0","0x1.0p+1","0x1.8p+1","0x1.0p+2"],["0x1.4p+2","0x1.8p+2","0x1.cp+2","0x1.0p+3"]],"alternative":"greater"}
{"id":"invalid-alternative","operation":"stratified-test","target":[["0x1.0p+0","0x1.0p+1","0x1.8p+1","0x1.0p+2"],["0x1.4p+2","0x1.8p+2","0x1.cp+2","0x1.0p+3"]],"control":[["0x1.0p+0","0x1.0p+1","0x1.8p+1","0x1.0p+2"],["0x1.4p+2","0x1.8p+2","0x1.cp+2","0x1.0p+3"]],"alternative":"two-sided"}
```

期待値は独立実装から生成してはならない。W-a親が外部参照実装という第三手段で導出し、literal化して
レビュー確認する。

### S2-2b.4 A前 report

3 reportは§S2-1.1のcanonical bytesで符号化し、次のcontent-addressed tracked pathへQで同時導入する。

```text
output/freeze-permanent/reports/verification-<raw_sha256>.json
output/freeze-permanent/reports/projection-<raw_sha256>.json
output/freeze-permanent/reports/wal-audit-<raw_sha256>.json
```

`report_type` の許可値は上記3種とS2-1.5の `generation-search` のexact 4値だけである。未知type、
filename/hash不一致、Q treeにないreportを拒否する。

3 report共通の `subjects` は fixed-order exact 4 elements、各要素exact `{kind,sha256}` である。

```json
[
  {"kind":"known","sha256":"<64hex>"},
  {"kind":"measurement","sha256":"<64hex>"},
  {"kind":"holdout","sha256":"<64hex>"},
  {"kind":"receipt","sha256":"<64hex>"}
]
```

verification reportは exact 6 fields。

```text
schema_version = "freeze-bundle-verification-report/v1"
validation_head
generation_number
subjects
results
aggregate
```

projection reportも exact 6 fields。

```text
schema_version = "freeze-transition-projection-report/v1"
validation_head
generation_number
subjects
results
aggregate
```

WAL audit reportは exact 9 fields。

```text
schema_version = "freeze-wal-audit-report/v1"
validation_head
generation_number
h_gen
subjects
wal_sources
observation_count
results
aggregate
```

- `validation_head` は3 reportで同一の40hex `Q^`。存在・到達可能性・Qとのparent関係を検査する。
- `generation_number` はnon-bool integer N≥1でbundleと一致する。
- WAL reportの `h_gen` はreceiptから再導出した40hex、`wal_sources` は§S2-1.7と同順・同値、
  `observation_count` はnon-bool non-negative integerでaudit入力と一致する。
- `results` は§S2-4の当該ordered registryをexactに1回ずつ持つarray。`aggregate` は`pass|fail`で、
  actual result列からのみ導出する。A/resolverが受理できるのは`pass`だけ。
- 全report hashは当該canonical raw bytesから計算する。report本文やpathをapproval後に再生成・差替えせず、
  `H_v` reachable historyでQ導入後のM/D/R/C/Tを拒否する。

owner: WAL predicate **W-b**、report schema/lineage predicate **W-c**、Q/A execution **W-e**。

---

## §S2-3 observation 伝播と legacy adapter registry

### S2-3.1 freeze_identity

exact 10 keys:

```text
schema_version
lane
generation_number
pointer
receipt
approval
bundle_digest_sha256
generation_commit
generation_basis_commit
artifacts
```

| field | exact 型・literal・null規則 |
|---|---|
| `schema_version` | string literal `freeze-bundle-identity/v1`。null不可 |
| `lane` | string enum `legacy|permanent`。null不可 |
| `generation_number` | non-bool integer。legacyはexact `0`、permanentは`N>=1` |
| `pointer` | exact `{path,raw_sha256}`。両laneで非null。pathは解決したactive pointer、hashはそのraw SHA-256 |
| `receipt` | legacyはexact null、permanentはexact `{path,raw_sha256}` |
| `approval` | legacyはexact null、permanentはexact `{path,raw_sha256}` |
| `bundle_digest_sha256` | legacyはexact null、permanentはlowercase 64hex |
| `generation_commit` | legacyはexact null、permanentはlowercase 40hex G |
| `generation_basis_commit` | legacyはexact null、permanentはlowercase 40hex H_gen (`G^`) |
| `artifacts` | exact object keys `known`,`measurement`,`holdout`。全3値非null |

`pointer` / `receipt` / `approval` refはexact 2 keysで、`path` は正規repo path、`raw_sha256` は64hex。
各artifact refはexact 3 keys `{path,raw_sha256,schema_version}`。artifactのnull規則は次で固定する。

| lane | known schema | measurement schema | holdout schema |
|---|---|---|---|
| legacy | `null` | `null` | `8b-holdout-freeze/v1` |
| permanent | `s1-known-axes-freeze/v2` | `s1-measurement-freeze/v3` | `8b-holdout-freeze/v3` |

permanentの3 artifact generationはtop-levelと同じN。legacyのpath/hashはg0 pointer literalと一致する。
laneとnull/non-null組合せを推測補正せず、表外の組合せを拒否する。

### S2-3.2 static verification observation

`freeze_verification_observation` は exact 4 keys。

```text
schema_version = "freeze-verification-observation/v1"
validation_head
aggregate
reports
```

report elementは exact 5 keys。

```text
subject
subject_sha256
schema_version
report_sha256
aggregate
```

legacy順は pointer/known/measurement/holdout、permanent順は
pointer/approval/receipt/known/measurement/holdout。`report_sha256` はactual result列を含む canonical report
hashであり、registry ID列挙だけから作ってはならない。

- top-level `validation_head` は40hex H_v、`aggregate` は`pass|fail`。campaignへ伝播できるのはpassのみ。
- report `subject` は上記順のenum、`subject_sha256` / `report_sha256` は64hex、report `aggregate` は
  `pass|fail`。top-level aggregateは全report aggregateから再導出する。
- report `schema_version` はstringまたはlegacy未装備時だけnull。legacy known/measurementはnull、
  legacy holdoutは`8b-holdout-freeze/v1`、pointerとpermanent全subjectは各exact schema literal。
- report arrayの件数、順序、subject/hash/schema対応をexactに検査し、欠落reportをpass扱いしない。

### S2-3.3 launch observation

`freeze_launch_observation` は exact 5 keys。

```text
schema_version = "freeze-launch-observation/v1"
validation_head
bundle_identity_sha256
live_scan_report_sha256
aggregate
```

campaign開始に使用できる aggregateは`pass`のみ。

- `validation_head` は40hex H_v、`bundle_identity_sha256` は§S2-3.1 canonical bytesの64hex、
  `live_scan_report_sha256` は§S2-10 report canonical bytesの64hex、`aggregate` は`pass|fail`。
- 5 fieldはいずれもnull不可。static observationと同じH_v/bundle identityに対するlaunch結果でなければ
  拒否し、campaignへ伝播できるのはpassだけ。

### S2-3.4 WAL/report/judge/calibration

#### 将来campaign-start v2

WAL wrapperは現行exact `{variant,stage,env_tag,ts,payload}` を維持する。`variant`,`stage`,`env_tag` は
nonempty string、`ts` はboolでないfinite JSON number、`payload` はobjectであり、未知wrapper keyを
拒否する。

S-1 campaign-start payloadは exact 7 keys。

```text
event
event_schema = "s1-campaign-start/v2"
campaign_role
ts
freeze_identity
freeze_verification_observation
freeze_launch_observation
```

- `event=="campaign-start"`、`event_schema=="s1-campaign-start/v2"`。
- `campaign_role` は`floor|block1|block2`、`ts` はnonempty RFC3339 string。
- 3 freeze fieldは§S2-3.1/3.2/3.3のexact nonnull objectで、verification/launch aggregateはpass。

8b campaign-start payloadは exact 9 keys。

```text
event
event_schema = "8b-oracle-campaign-start/v2"
manifest_sha256
block_id
campaign_id
execution_receipt
freeze_identity
freeze_verification_observation
freeze_launch_observation
```

- `event=="campaign-start"`、`event_schema=="8b-oracle-campaign-start/v2"`。
- `manifest_sha256` は64hex、`block_id` / `campaign_id` はnonempty string、`execution_receipt` は
  current execution-guard exact objectでnull不可。
- 3 freeze fieldは上記と同じnonnull/pass制約。v2 payloadでfield欠落/nullを許さない。

#### g1 source WAL専用の旧campaign-start grammar

g1のmeasurementを生成する既存3 WALだけは `event_schema` と3 freeze objectを持たない。A前auditの
`audit.campaign-start` は、receiptでraw blobが固定されたfloor/block1/block2 WALに限り、次を
**旧grammarとして別branchで**受理する。

```text
wrapper exact keys: variant,stage,env_tag,ts,payload
variant = "s1-campaign"
stage = "s1-session"
env_tag = wal_source.env_tag (nonempty string)
ts = boolでないfinite JSON number
payload exact keys: event,campaign_role,ts
payload.event = "campaign-start"
payload.campaign_role = floor|block1|block2 (wal_sourceと一致)
payload.ts = nonempty string
record ordinal = 1
```

旧branchで `event_schema` またはfreeze objectを補作せず、将来campaignのlaunch、g2+ WAL source、
campaign-start v2 consumerへ流用しない。この受理はg1 migration audit専用で、3 WALのpath/blob/raw hash
束縛を緩めない。

#### S-1 report v2

S-1 v2 reportはexact 10 keys。

```text
schema_version
freeze_identity
freeze_verification_observation
freeze_launch_observation
hard_gates
comparisons
families
effect_sizes
budget
generated_at_head
```

- `schema_version=="s1-direct-comparison-report/v2"`。現行v1の`freeze_ref`は禁止する。
- `hard_gates`,`families`,`effect_sizes`,`budget` はobject、`comparisons` はarray、`generated_at_head` は40hex。
- 3 performance WALの3 freeze objectがcanonical JSON値として全一致し、両observationがpassなら、
  reportの3 fieldへその値をnonnullでcopyする。
- 欠落・schema違反・WAL間不一致・nonpassなら3 fieldを**全てnull**とし、`hard_gates` のfreeze contract
  gateをfailにして全comparisonを判定不能にする。1 fieldだけnonnullの部分状態を拒否する。

#### Oracle observations / verdict v2

Oracle observations v2はexact 10 keys。

```text
schema_version
manifest_kind
manifest_sha256
n_per_cell
expected_cells
rows
freeze_identity
freeze_verification_observation
freeze_launch_observation
freeze_contract_reason_codes
```

- `schema_version=="8b-oracle-observations/v2"`、`manifest_kind` は`official|legacy`、
  `manifest_sha256` は64hex、`n_per_cell` はboolでない正整数、`expected_cells` / `rows` はarray。
- 3 freeze fieldはpass時にexact objectで全てnonnull、reason arrayは空。
- 欠落・schema違反・campaign間不一致・nonpass時は3 fieldを全てnull、reason arrayをnonemptyとし、
  該当campaignの全rowを`protocol_violation`にする。部分nonnullを拒否する。

Oracle verdict v2もexact 10 keys。

```text
schema_version
manifest_sha256
n_per_cell
status
reasons
holdouts
freeze_identity
freeze_verification_observation
freeze_launch_observation
freeze_contract_reason_codes
```

- `schema_version=="8b-oracle-verdict/v2"`、`manifest_sha256` / `n_per_cell` はobservationsと一致、
  `status` は`determinate|indeterminate`、`reasons` はarray、`holdouts` はobject。
- 後4 fieldはobservationsからcanonical JSON値をそのままcopyする。judgeがresolverを再実行して置換しない。
- 3 fieldのいずれかがnullまたはreason arrayがnonemptyなら `status=="indeterminate"`。

`freeze_contract_reason_codes` とS-1 freeze-contract hard gateが使えるcodeは、重複なしUTF-8昇順の
次のexact集合の部分集合だけである。未知codeを拒否する。

```text
dependency.freeze_observation_missing
schema.freeze_observation_invalid
contract.freeze_identity_mismatch
contract.freeze_observation_mismatch
contract.freeze_observation_nonpass
dependency.freeze_launch_missing
schema.freeze_launch_invalid
contract.freeze_launch_mismatch
contract.freeze_launch_nonpass
```

#### calibration v2

calibration successor path:

```text
output/env/<env_tag>/calibration/s1_verify_extime.v2.g<N>.json
```

top-levelはexact 13 keys。

```text
schema_version
config_name
env_tag
ccbench_commit
genome
freeze_identity
freeze_verification_observation
freeze_launch_observation
configuration_provenance
candidates
chosen_extime
limit_s
decision_rule
```

- `schema_version=="s1-verify-extime-calibration/v2"`。`config_name`,`env_tag`,`genome`,`decision_rule` は
  nonempty string、`ccbench_commit` は40hex、`chosen_extime` / `limit_s` はboolでない正整数。
- 3 freeze fieldはexact nonnull objectでverification/launch aggregateはpass。欠落・null・不一致・
  nonpassなら上記reason codeでcalibration生成自体を拒否し、null入りv2を発行しない。
- `configuration_provenance` はexact 12 keys
  `{workload,workload_flags,subset_name,gate_predicate,template_patch,src_token,binary_hash,build_cached,configure_cmd,build_cmd,free_disk_gb_at_start,known_entry_pointer}`。
  `known_entry_pointer=="/entries/read-heavy/system_gate"`、`build_cached` はbool、
  `free_disk_gb_at_start` はfinite JSON number、他はnonempty stringまたは既存exact object。
  v1の`freeze_path`,`freeze_frozen_at_head`,`freeze_system_gate`は禁止する。
- `candidates` は1〜3件、extimeが`[3]`,`[3,6]`,`[3,6,10]`のいずれかのprefix。各要素はexact 11 keys
  `{extime,run_walltime_s,trace_files,trace_bytes,trace_lines,verifier_walltime_s,maxrss_gb,txns,edges,verdict,certified}`。
  `extime/trace_files/trace_bytes/trace_lines/txns/edges` はnon-bool non-negative integer、walltime/maxrssは
  finite non-negative number、`verdict` はnonempty string、`certified` はbool。全field null不可。

歴史物 `output/env/linux-baremetal/calibration/s1_verify_extime.json` は変更しない。

実物根拠: 現行 WAL writer、S-1 report、oracle report/judge、calibration。  
owner: schema carrier **W-a**、全伝播 **W-d**。

### S2-3.5 legacy adapter registry

g0は生dictや新schemaへの推測変換をしない。exact adapterは次の3件。

| adapter | raw root | strict parse後の返却型 |
|---|---|---|
| `legacy-known/v0` | legacy known path + exact SHA-256 | `LegacyKnownArtifact` |
| `legacy-measurement/v0` | legacy measurement path + exact SHA-256 | `LegacyMeasurementArtifact` |
| `legacy-holdout/v1` | legacy holdout path + exact SHA-256 | `LegacyHoldoutArtifact` |

各adapterはraw bytesを一度だけ読み、次の3段だけを順にgateとする。

1. g0 pointer literalのpathとraw SHA-256にexact一致すること。
2. duplicate key / NaN / Infinity / top-level非objectを拒否するstrict JSON parse。
3. family tag、raw bytes/hash、deep-immutable parsed objectを上表のexact型へ変換できること。

**現行 full verifierへの委譲はg0 gateに含めない。** known/measurementのdangling `frozen_at_head`、
holdoutの`design_source` driftを再検査すると現物3件すべてが拒否され、g0 bundleを構築できないためである。
g0 adapterのrefusal集合は `raw root不一致 | strict parse不能 | 型変換違反` の3種類だけであり、
source/head/design-sourceの現在有効性を主張しない。例外文字列から別分類を推測しない。
g0 launchはさらに§S2-10のlive scanを通すが、live scanもsource/headの現在有効性を証明しない。

PREDICTION_SCHEMAはbundle generation分岐とする。

```text
g0 pointer  -> prediction v1のみ
g1+ pointer -> prediction v2のみ
```

W-dで両branchをdormant実装し、Xのpointer更新だけで切り替える。別configやW-f code変更を置かない。

owner: adapter **W-a**、g0 resolver **W-c**、consumer/launch **W-d**。

---

## §S2-4 check-ID registry

### S2-4.1 report grammar

check-ID grammar:

```regex
^[a-z][a-z0-9]*(\.[a-z][a-z0-9-]*)+$
```

reason code grammarは全schemaで一つだけである。

```regex
^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$
```

dotはちょうど1個。kebab-caseを禁止する。未知reason codeはreport全体をerrorにする。

resultは exact 4 keys。

```json
{"check_id":"measurement.cells","status":"pass","reason_code":null,"blocked_by":[]}
```

- statusは`pass|error|not_evaluated`。
- passはreason null、blocked_by空。
- errorは当該IDのreason、blocked_by空。
- not_evaluatedは`dependency.blocked`、blocked_by 1件以上。
- blocked_byは同registryの既存ID、重複なし、registry順、当該IDより前、かつstatusがpassでないIDだけ。
- error/not_evaluatedが1件でもaggregateはfail。
- cycle専用predicateは置かない。strict-earlier規則がcycleを構造的に排除する。
- aggregateのfail-open変異は独立候補とする。

`blocked_by` 遷移の根拠は§S2-4.5 TSVの `direct_dependencies` だけである。直接依存のうちnonpassのIDを
registry順に**全件**入れて `not_evaluated` とし、推移依存や無関係な先行IDを追加しない。直接依存が
全てpassならpredicateを評価してpass/errorのどちらかにし、空dependencyのIDをnot_evaluatedにしない。
これにより同一入力のerror/not_evaluated分岐を実装者判断にしない。

report envelope自身のordered registryは次のexact 5 IDである。

```text
report.exact-id-set
report.result-shape
report.blocked-by
report.reason-code
report.aggregate
```

### S2-4.2 四型

型変換は次だけである。

```text
verify_candidate(raw)                       -> CandidateArtifact
register(candidate, production_root, test_root, receipt)
                                              -> RegisteredInactiveArtifact
approve(registered, approval)               -> ApprovedInactiveArtifact
activate(approved triple, pointer)           -> ActiveOfficialBundle
```

`lifecycle=` flag、生dict、型cast、missing-root特例による昇格を禁止する。

family Fのordered registry:

```text
candidate(F):
  document.raw-readable
  document.strict-json
  schema.version
  schema.exact-keys
  schema.generation-fields
  <F-specific IDs>

registered-inactive(F):
  document.raw-readable
  output.production-root
  output.test-manifest-root
  document.strict-json
  schema.version
  schema.exact-keys
  schema.generation-fields
  <F-specific IDs>
  lineage.introduction
  lineage.generation-diff
  input.generation-tree-blob
  lineage.receipt-binding

approved-inactive(F):
  registered-inactive(F)
  authorization.approval-reference
  authorization.report-hashes
  authorization.bundle-digest
  authorization.approval-topology
  <U-A1 check if selected>

active-official(F):
  approved-inactive(F)
  lineage.pointer-chain
  lineage.bundle-lockstep
  authorization.revocation-state
  authorization.cancellation-state
  lineage.active-unique
```

candidate registryに`output.*root`を含めない。

family-specific ordered IDs:

```text
known.what
known.ccbench-pin
known.selection-rules
known.entries
known.s1b-pairing
known.reference-values-note
known.source-records
known.source-paths
known.source-tree-blobs
known.enumeration-snapshot
known.final-record-count
```

```text
measurement.what
measurement.known-reference
measurement.ccbench-pin
measurement.cells
measurement.comparisons
measurement.s1b-pairing
measurement.operating-point
measurement.workload-flags
measurement.master-seed
measurement.schedule
measurement.schedule-hash
measurement.observations-shape
measurement.observations-bijection
measurement.wal-source-pointer-shape
measurement.analysis-shape
measurement.analysis-statistics
measurement.analysis-p-values
measurement.analysis-gates
measurement.analysis-effects
measurement.analysis-families
```

```text
holdout.what
holdout.lifecycle-stage
holdout.design-source
holdout.known-reference
holdout.match-convention
holdout.search-declaration
holdout.search-enumeration
holdout.holdouts
holdout.unknownness-snapshot
holdout.positive-control
holdout.derangement
holdout.confirmation
holdout.lifecycle-fields
holdout.measurement-closure
```

この表示順はreport順でもある。direct dependencyは後記§S2-4.5の機械読取可能表だけを正本とし、
「same-stage」「上から順」等の暗黙依存を追加してはならない。

### S2-4.3 governance registry

g1 receipt:

```text
receipt.schema
receipt.generation
receipt.g-hgen-binding
receipt.inventory
receipt.successors
receipt.projection
receipt.metadata-moves
receipt.audit-input
receipt.holdout-confirmation
receipt.search-report-path
receipt.search-report-bytes
receipt.search-report-content
receipt.output-tree-blobs
receipt.input-tree-closure
receipt.commit-topology
```

future receiptは`receipt.inventory/projection/metadata-moves`を
`receipt.predecessors`に置換する。

approval:

```text
approval.schema
approval.filename
approval.components
approval.report-hashes
approval.report-paths
approval.report-bytes
approval.report-subjects
approval.report-aggregate
approval.report-validation-head
approval.bundle-digest
approval.receipt-reference
approval.production-root-topology
approval.manifest-root-topology
approval.report-topology
approval.commit-ancestry
approval.commit-merge
approval.commit-diff
approval.human-trailer
approval.unique-selection
approval.revocation
<U-A1 check>
```

pointer:

```text
pointer.schema
pointer.filename
pointer.genesis
pointer.parent
pointer.generation-step
pointer.bundle-lockstep
pointer.receipt-reference
pointer.approval-reference
pointer.no-fork
pointer.no-gap
pointer.no-rollback
pointer.revocation
pointer.cancellation
pointer.unique-tip
pointer.x-commit
<U-A1 check if required>
```

revocation:

```text
revocation.schema
revocation.target
revocation.unique
revocation.commit-topology
revocation.commit-merge
revocation.commit-diff
revocation.human-trailer
revocation.immutable
```

cancellation:

```text
cancellation.schema
cancellation.target
cancellation.fork-loser
cancellation.unique
cancellation.commit-topology
cancellation.commit-merge
cancellation.commit-diff
cancellation.human-trailer
cancellation.immutable
```

topology系IDの責務は単一理由に分割する。`approval.commit-ancestry`、
`revocation.commit-topology`、`cancellation.commit-topology` は対象commitへの到達可能性・必要な祖先/
parent関係だけを検査し、diff、parent count、trailerを検査しない。各 `*.commit-diff` は
`diff-tree --no-renames` のpath/status集合だけ、各 `*.commit-merge` はparent count `==1`だけ、
各 `*.human-trailer` はraw/parsed `AI-Agent: none`だけを検査する。したがって§S2-9の各fixtureは表に記した
1 checkだけを第一失敗にできる。

### S2-4.4 legacy、audit、launch、prediction registry

legacy:

```text
legacy.known-raw-root
legacy.known-strict-json
legacy.known-type
legacy.measurement-raw-root
legacy.measurement-strict-json
legacy.measurement-type
legacy.holdout-raw-root
legacy.holdout-strict-json
legacy.holdout-type
```

WAL audit:

```text
audit.input-binding
audit.wal-blob
audit.campaign-start
audit.session-interval
audit.wrapper-identity
audit.schedule-bijection
audit.value-origin
audit.aggregate
```

launch:

```text
launch.argument-type
launch.active-resolution
launch.enumeration-stable
launch.exemptions
launch.expected-hits
launch.positive-control
launch.bound-artifact-stable
launch.aggregate
```

prediction v2:

```text
prediction.schema
prediction.body
prediction.legacy-field-absent
prediction.semantic-closure
prediction.source-tree-blobs
prediction.introduction
prediction.parent-basis
prediction.immutable
prediction.published-type
prediction.bundle-generation-schema
```

### S2-4.5 reason code単一対応表

以下のTSVがcheck-ID registryの機械読取可能な正本である。列はexact
`check_id<TAB>field_pointer<TAB>direct_dependencies<TAB>reason_code`。dependencyはJSON arrayで、
**直接辺だけ**をregistry順に書く。推移辺を補作しない。

`field_pointer` はJSON Pointer pattern (`*` はその位置の全object key/array indexを表す)、または次の
closed enumの拡張pointerである。

```text
@raw[/<name>]            subject raw bytesまたはその派生filename/family view
@git/<name>             捕捉済みGit graph/tree/diff上の値
@derived/<name>         複数JSON fieldから一意再導出する値
@report/<name>          canonical report envelope/body上の値
@runtime/<name>         launch/use-timeで捕捉した値
```

表にないcheck-ID、pointer、dependency edge、reason codeを拒否する。U-A1行だけは裁定後に
§S2-11の手順でversioned registryへ追加する。

#### S2-4.5.1 report envelope / family lifecycle共通

```text
check_id	field_pointer	direct_dependencies	reason_code
report.exact-id-set	/results/*/check_id	[]	schema.check_id_set_mismatch
report.result-shape	/results	["report.exact-id-set"]	schema.result_shape_invalid
report.blocked-by	/results/*/blocked_by	["report.result-shape"]	dependency.blocked_by_invalid
report.reason-code	/results/*/reason_code	["report.result-shape"]	schema.unknown_reason_code
report.aggregate	/aggregate	["report.blocked-by","report.reason-code"]	contract.aggregate_mismatch
document.raw-readable	@raw	[]	document.read_failed
output.production-root	@raw	["document.raw-readable"]	output.production_root_mismatch
output.test-manifest-root	@raw	["document.raw-readable"]	output.test_manifest_root_mismatch
document.strict-json	@raw	["document.raw-readable"]	document.json_invalid
schema.version	/schema_version	["document.strict-json"]	schema.version_mismatch
schema.exact-keys	/	["schema.version"]	schema.keys_mismatch
schema.generation-fields	/generation_number	["schema.exact-keys"]	schema.generation_fields_invalid
lineage.introduction	@git/artifact-introduction	["schema.generation-fields"]	lineage.introduction_invalid
lineage.generation-diff	@derived/generation-transition-diff	["lineage.introduction"]	lineage.generation_diff_invalid
input.generation-tree-blob	@git/H_gen-input-blobs	["lineage.introduction"]	input.generation_tree_blob_mismatch
lineage.receipt-binding	@derived/receipt-subject-binding	["lineage.generation-diff","input.generation-tree-blob"]	lineage.receipt_binding_mismatch
authorization.approval-reference	@derived/approval-reference	["lineage.receipt-binding"]	authorization.approval_reference_invalid
authorization.report-hashes	@report/approval-reports	["authorization.approval-reference"]	authorization.report_hash_mismatch
authorization.bundle-digest	@derived/bundle-digest	["authorization.report-hashes"]	authorization.bundle_digest_mismatch
authorization.approval-topology	@git/A	["authorization.bundle-digest"]	authorization.approval_topology_invalid
lineage.pointer-chain	@derived/pointer-chain	["authorization.approval-topology"]	lineage.pointer_chain_invalid
lineage.bundle-lockstep	@derived/active-bundle	["lineage.pointer-chain"]	lineage.bundle_lockstep_mismatch
authorization.revocation-state	@derived/revocation-state	["lineage.pointer-chain"]	authorization.bundle_revoked
authorization.cancellation-state	@derived/cancellation-state	["lineage.pointer-chain"]	authorization.pointer_cancelled
lineage.active-unique	@derived/live-tip	["lineage.bundle-lockstep","authorization.revocation-state","authorization.cancellation-state"]	lineage.active_ambiguous
```

#### S2-4.5.2 family semantic rows

```text
check_id	field_pointer	direct_dependencies	reason_code
known.what	/what	["schema.generation-fields"]	contract.known_what_mismatch
known.ccbench-pin	/ccbench_pin	["schema.generation-fields"]	input.known_ccbench_pin_mismatch
known.selection-rules	/selection_rules	["schema.generation-fields"]	contract.known_selection_rules_mismatch
known.entries	/entries	["schema.generation-fields"]	contract.known_entries_mismatch
known.s1b-pairing	/s1b_pairing	["schema.generation-fields"]	contract.known_s1b_pairing_mismatch
known.reference-values-note	/reference_values_note	["schema.generation-fields"]	contract.known_reference_values_mismatch
known.source-records	/source_closure/records	["schema.generation-fields"]	contract.known_source_records_mismatch
known.source-paths	/entries/*/*/sources	["schema.generation-fields"]	contract.known_source_paths_mismatch
known.source-tree-blobs	@git/H_gen-known-source-blobs	["known.source-records","known.source-paths"]	input.known_source_tree_blob_mismatch
known.enumeration-snapshot	/source_closure/file_enumerations	["schema.generation-fields"]	contract.known_enumeration_snapshot_mismatch
known.final-record-count	/source_closure	["known.source-records","known.enumeration-snapshot"]	contract.known_record_count_mismatch
measurement.what	/what	["schema.generation-fields"]	contract.measurement_what_mismatch
measurement.known-reference	/known_axes_freeze	["schema.generation-fields"]	dependency.measurement_known_reference_mismatch
measurement.ccbench-pin	/ccbench_pin	["schema.generation-fields"]	input.measurement_ccbench_pin_mismatch
measurement.cells	/cells	["schema.generation-fields"]	contract.measurement_cells_mismatch
measurement.comparisons	/comparisons	["schema.generation-fields"]	contract.measurement_comparisons_mismatch
measurement.s1b-pairing	/s1b_pairing	["schema.generation-fields"]	contract.measurement_s1b_pairing_mismatch
measurement.operating-point	/operating_point	["schema.generation-fields"]	contract.measurement_operating_point_mismatch
measurement.workload-flags	/workload_flags	["schema.generation-fields"]	contract.measurement_workload_flags_mismatch
measurement.master-seed	/master_seed	["schema.generation-fields"]	contract.measurement_master_seed_mismatch
measurement.schedule	/schedule	["schema.generation-fields"]	contract.measurement_schedule_mismatch
measurement.schedule-hash	/schedule_hash	["measurement.schedule"]	contract.measurement_schedule_hash_mismatch
measurement.observations-shape	/observations	["schema.generation-fields"]	schema.measurement_observations_invalid
measurement.observations-bijection	/observations/records	["measurement.schedule","measurement.observations-shape"]	contract.measurement_observation_bijection_mismatch
measurement.wal-source-pointer-shape	/observations/wal_sources	["measurement.observations-shape"]	schema.measurement_wal_pointer_invalid
measurement.analysis-shape	/analysis_results	["schema.generation-fields"]	schema.measurement_analysis_invalid
measurement.analysis-statistics	/analysis_results/comparisons/*/statistic_rank_sum_x2	["measurement.observations-bijection","measurement.analysis-shape"]	output.measurement_statistic_mismatch
measurement.analysis-p-values	/analysis_results/comparisons/*/p_permutation	["measurement.analysis-statistics"]	output.measurement_p_value_mismatch
measurement.analysis-gates	/analysis_results/comparisons/*/gates	["measurement.observations-bijection","measurement.analysis-shape"]	output.measurement_gate_mismatch
measurement.analysis-effects	/analysis_results/comparisons/*/effect_sizes	["measurement.observations-bijection","measurement.analysis-shape"]	output.measurement_effect_mismatch
measurement.analysis-families	/analysis_results/families	["measurement.analysis-p-values","measurement.analysis-gates"]	output.measurement_family_mismatch
holdout.what	/what	["schema.generation-fields"]	contract.holdout_what_mismatch
holdout.lifecycle-stage	/lifecycle_stage	["schema.generation-fields"]	contract.holdout_lifecycle_stage_mismatch
holdout.design-source	/design_source	["schema.generation-fields"]	input.holdout_design_source_mismatch
holdout.known-reference	/known_axes_freeze	["schema.generation-fields"]	dependency.holdout_known_reference_mismatch
holdout.match-convention	/match_convention	["schema.generation-fields"]	contract.holdout_match_convention_mismatch
holdout.search-declaration	/search	["schema.generation-fields"]	contract.holdout_search_declaration_mismatch
holdout.search-enumeration	/search	["holdout.search-declaration"]	contract.holdout_search_enumeration_mismatch
holdout.holdouts	/holdouts	["schema.generation-fields"]	contract.holdout_definition_mismatch
holdout.unknownness-snapshot	/search	["holdout.search-enumeration","holdout.holdouts"]	contract.holdout_snapshot_mismatch
holdout.positive-control	/positive_control	["holdout.search-enumeration"]	contract.holdout_positive_control_mismatch
holdout.derangement	/derangement	["schema.generation-fields"]	contract.holdout_derangement_mismatch
holdout.confirmation	@derived/holdout-confirmation	["holdout.search-enumeration","holdout.holdouts"]	contract.holdout_confirmation_mismatch
holdout.lifecycle-fields	@derived/holdout-lifecycle-fields	["holdout.lifecycle-stage"]	contract.holdout_lifecycle_fields_mismatch
holdout.measurement-closure	/measurement_closure	["holdout.lifecycle-stage"]	contract.holdout_measurement_closure_mismatch
```

#### S2-4.5.3 receipt / approval / pointer / RV / CX

```text
check_id	field_pointer	direct_dependencies	reason_code
receipt.schema	/	[]	schema.receipt_invalid
receipt.generation	/generation_number	["receipt.schema"]	lineage.receipt_generation_mismatch
receipt.g-hgen-binding	@derived/G-H_gen	["receipt.generation"]	lineage.receipt_commit_mismatch
receipt.inventory	/legacy_inventory	["receipt.generation"]	lineage.receipt_inventory_mismatch
receipt.predecessors	/predecessors	["receipt.generation"]	lineage.receipt_predecessor_mismatch
receipt.successors	/successors	["receipt.generation"]	lineage.receipt_successor_mismatch
receipt.projection	/projections	["receipt.inventory","receipt.successors"]	contract.projection_mismatch
receipt.metadata-moves	/projections/*/metadata_sources	["receipt.projection"]	contract.metadata_pointer_mismatch
receipt.audit-input	/observation_audit_input	["receipt.successors"]	input.wal_audit_input_mismatch
receipt.holdout-confirmation	/holdout_confirmation	["receipt.successors"]	contract.holdout_confirmation_mismatch
receipt.search-report-path	@report/generation-search-path	["receipt.holdout-confirmation"]	output.search_report_missing
receipt.search-report-bytes	@report/generation-search-raw	["receipt.search-report-path"]	output.search_report_hash_mismatch
receipt.search-report-content	@report/generation-search-body	["receipt.search-report-bytes"]	contract.search_report_mismatch
receipt.output-tree-blobs	@git/G-output-blobs	["receipt.g-hgen-binding","receipt.successors"]	output.generation_blob_mismatch
receipt.input-tree-closure	@git/H_gen-input-closure	["receipt.g-hgen-binding","receipt.successors"]	input.generation_closure_mismatch
receipt.commit-topology	@git/R	["receipt.g-hgen-binding"]	contract.receipt_commit_topology_mismatch
approval.schema	/	[]	schema.approval_invalid
approval.filename	@raw/filename	["approval.schema"]	authorization.approval_filename_mismatch
approval.components	/components	["approval.schema"]	authorization.approval_component_mismatch
approval.report-hashes	/reports	["approval.components"]	authorization.report_hash_mismatch
approval.report-paths	@report/three-paths	["approval.report-hashes"]	output.approval_report_missing
approval.report-bytes	@report/three-raw-bytes	["approval.report-paths"]	authorization.report_hash_mismatch
approval.report-subjects	@report/three-subjects	["approval.report-bytes"]	authorization.report_subject_mismatch
approval.report-aggregate	@report/three-aggregate	["approval.report-bytes"]	authorization.report_not_pass
approval.report-validation-head	@report/three-validation-head	["approval.report-bytes"]	authorization.report_validation_head_invalid
approval.bundle-digest	/bundle_digest	["approval.components","approval.report-hashes"]	authorization.bundle_digest_mismatch
approval.receipt-reference	@derived/approval-receipt	["approval.components"]	authorization.approval_receipt_mismatch
approval.production-root-topology	@git/L_prod	["approval.receipt-reference"]	lineage.production_root_topology_invalid
approval.manifest-root-topology	@git/L_manifest	["approval.production-root-topology"]	lineage.manifest_root_topology_invalid
approval.report-topology	@git/Q	["approval.report-paths","approval.report-validation-head","approval.manifest-root-topology"]	lineage.report_topology_invalid
approval.commit-ancestry	@git/A-ancestry	["approval.report-topology"]	authorization.approval_ancestry_invalid
approval.commit-merge	@git/A-parents	["approval.commit-ancestry"]	authorization.approval_merge_forbidden
approval.commit-diff	@git/A-diff	["approval.commit-ancestry"]	authorization.approval_diff_invalid
approval.human-trailer	@git/A-trailers	["approval.commit-ancestry"]	authorization.human_trailer_invalid
approval.unique-selection	@derived/approval-selection	["approval.bundle-digest"]	authorization.approval_selection_ambiguous
approval.revocation	@derived/approval-revocation	["approval.unique-selection"]	authorization.bundle_revoked
pointer.schema	/	[]	schema.pointer_invalid
pointer.filename	@raw/filename	["pointer.schema"]	lineage.pointer_filename_mismatch
pointer.genesis	@derived/g0-genesis	["pointer.schema"]	lineage.pointer_genesis_invalid
pointer.parent	/parent_active_sha256	["pointer.schema"]	lineage.pointer_parent_invalid
pointer.generation-step	/generation_number	["pointer.parent"]	lineage.pointer_generation_step_invalid
pointer.bundle-lockstep	/artifacts	["pointer.generation-step"]	lineage.bundle_lockstep_mismatch
pointer.receipt-reference	/receipt	["pointer.bundle-lockstep"]	lineage.pointer_receipt_mismatch
pointer.approval-reference	/approval_sha256	["pointer.bundle-lockstep"]	authorization.approval_reference_invalid
pointer.no-fork	@derived/pointer-children	["pointer.parent"]	lineage.pointer_fork
pointer.no-gap	@derived/pointer-generations	["pointer.generation-step"]	lineage.generation_gap
pointer.no-rollback	@derived/pointer-tip	["pointer.generation-step"]	lineage.rollback_forbidden
pointer.revocation	@derived/pointer-revocation	["pointer.approval-reference"]	authorization.bundle_revoked
pointer.cancellation	@derived/pointer-cancellation	["pointer.parent"]	authorization.pointer_cancelled
pointer.unique-tip	@derived/live-tip	["pointer.no-fork","pointer.no-gap","pointer.no-rollback","pointer.revocation","pointer.cancellation"]	lineage.active_ambiguous
pointer.x-commit	@git/X	["pointer.approval-reference","pointer.unique-tip"]	authorization.activation_topology_invalid
revocation.schema	/	[]	schema.revocation_invalid
revocation.target	/bundle_digest	["revocation.schema"]	authorization.revocation_target_invalid
revocation.unique	@derived/revocation-count	["revocation.target"]	authorization.revocation_duplicate
revocation.commit-topology	@git/RV-ancestry	["revocation.target"]	authorization.revocation_topology_invalid
revocation.commit-merge	@git/RV-parents	["revocation.commit-topology"]	authorization.revocation_merge_forbidden
revocation.commit-diff	@git/RV-diff	["revocation.commit-topology"]	authorization.revocation_diff_invalid
revocation.human-trailer	@git/RV-trailers	["revocation.commit-topology"]	authorization.human_trailer_invalid
revocation.immutable	@git/RV-history	["revocation.unique","revocation.commit-merge","revocation.commit-diff"]	lineage.record_mutated
cancellation.schema	/	[]	schema.cancellation_invalid
cancellation.target	/pointer_sha256	["cancellation.schema"]	authorization.cancellation_target_invalid
cancellation.fork-loser	@derived/CX-fork-set	["cancellation.target"]	lineage.rollback_forbidden
cancellation.unique	@derived/cancellation-count	["cancellation.target"]	authorization.cancellation_duplicate
cancellation.commit-topology	@git/CX-ancestry	["cancellation.fork-loser"]	authorization.cancellation_topology_invalid
cancellation.commit-merge	@git/CX-parents	["cancellation.commit-topology"]	authorization.cancellation_merge_forbidden
cancellation.commit-diff	@git/CX-diff	["cancellation.commit-topology"]	authorization.cancellation_diff_invalid
cancellation.human-trailer	@git/CX-trailers	["cancellation.commit-topology"]	authorization.human_trailer_invalid
cancellation.immutable	@git/CX-history	["cancellation.unique","cancellation.commit-merge","cancellation.commit-diff"]	lineage.record_mutated
```

future receipt registryでは`receipt.inventory/receipt.projection/receipt.metadata-moves`を除き、
`receipt.predecessors`を同じ位置へ入れる。そのためfutureの`receipt.successors`は
`["receipt.generation","receipt.predecessors"]`、他の直接辺は同表のままとする。この型変換以外の
条件分岐を認めない。

#### S2-4.5.4 legacy / audit / launch / prediction

```text
check_id	field_pointer	direct_dependencies	reason_code
legacy.known-raw-root	@raw/known	[]	output.legacy_root_mismatch
legacy.known-strict-json	@raw/known	["legacy.known-raw-root"]	document.json_invalid
legacy.known-type	@derived/LegacyKnownArtifact	["legacy.known-strict-json"]	schema.legacy_type_invalid
legacy.measurement-raw-root	@raw/measurement	[]	output.legacy_root_mismatch
legacy.measurement-strict-json	@raw/measurement	["legacy.measurement-raw-root"]	document.json_invalid
legacy.measurement-type	@derived/LegacyMeasurementArtifact	["legacy.measurement-strict-json"]	schema.legacy_type_invalid
legacy.holdout-raw-root	@raw/holdout	[]	output.legacy_root_mismatch
legacy.holdout-strict-json	@raw/holdout	["legacy.holdout-raw-root"]	document.json_invalid
legacy.holdout-type	@derived/LegacyHoldoutArtifact	["legacy.holdout-strict-json"]	schema.legacy_type_invalid
audit.input-binding	/observation_audit_input	[]	input.wal_audit_input_mismatch
audit.wal-blob	@git/H_gen-WAL-blobs	["audit.input-binding"]	input.wal_blob_mismatch
audit.campaign-start	@derived/WAL-campaign-start	["audit.wal-blob"]	contract.wal_campaign_start_mismatch
audit.session-interval	@derived/WAL-session-intervals	["audit.wal-blob"]	contract.wal_session_interval_invalid
audit.wrapper-identity	@derived/WAL-wrapper-identities	["audit.session-interval"]	contract.wal_wrapper_identity_mismatch
audit.schedule-bijection	/observations/records	["audit.session-interval"]	contract.measurement_observation_bijection_mismatch
audit.value-origin	/observations/records/*/source/value_origin_sha256	["audit.wal-blob","audit.schedule-bijection"]	contract.measurement_value_origin_mismatch
audit.aggregate	@report/wal-audit-aggregate	["audit.campaign-start","audit.wrapper-identity","audit.value-origin"]	authorization.wal_audit_failed
launch.argument-type	@runtime/argument	[]	schema.launch_argument_invalid
launch.active-resolution	@runtime/active-resolution	["launch.argument-type"]	lineage.active_resolution_invalid
launch.enumeration-stable	/enumeration	["launch.active-resolution"]	contract.live_enumeration_changed
launch.exemptions	/exemptions	["launch.active-resolution"]	contract.live_scan_exemption_invalid
launch.expected-hits	/holdouts	["launch.enumeration-stable","launch.exemptions"]	contract.live_expected_hits_mismatch
launch.positive-control	/positive_control	["launch.enumeration-stable"]	contract.live_positive_control_failed
launch.bound-artifact-stable	@runtime/bound-artifact-reread	["launch.active-resolution"]	contract.live_bound_artifact_changed
launch.aggregate	/aggregate	["launch.expected-hits","launch.positive-control","launch.bound-artifact-stable"]	authorization.launch_validation_failed
prediction.schema	/	[]	schema.prediction_invalid
prediction.body	/body_sha256	["prediction.schema"]	contract.prediction_body_mismatch
prediction.legacy-field-absent	/pre_oracle_head	["prediction.schema"]	schema.prediction_legacy_field_present
prediction.semantic-closure	/prediction_basis_tree/semantic_input_closure	["prediction.schema"]	input.prediction_semantic_closure_mismatch
prediction.source-tree-blobs	@git/H_pred-semantic-blobs	["prediction.semantic-closure"]	input.prediction_source_tree_blob_mismatch
prediction.introduction	@git/G_pred	["prediction.source-tree-blobs"]	lineage.prediction_introduction_invalid
prediction.parent-basis	@git/H_pred	["prediction.introduction"]	lineage.prediction_parent_basis_invalid
prediction.immutable	@git/G_pred-history	["prediction.introduction"]	lineage.prediction_record_mutated
prediction.published-type	@derived/PublishedPrediction	["prediction.parent-basis","prediction.immutable"]	schema.prediction_published_type_required
prediction.bundle-generation-schema	@derived/pointer-generation-prediction-schema	["prediction.published-type"]	schema.prediction_generation_schema_mismatch
```

以下はcheck/eventの人間向けindexである。check-ID行は上記TSVからの補助表示、Git/CLI/伝播event行は
check result外で使う追加のexact mappingである。check-ID行が競合する場合はTSVを正本とする。

| check/event | reason code |
|---|---|
| `document.raw-readable` | `document.read_failed` |
| `document.strict-json` | `document.json_invalid` |
| `output.production-root` | `output.production_root_mismatch` |
| `output.test-manifest-root` | `output.test_manifest_root_mismatch` |
| `schema.version` | `schema.version_mismatch` |
| `schema.exact-keys` | `schema.keys_mismatch` |
| `schema.generation-fields` | `schema.generation_fields_invalid` |
| `report.exact-id-set` | `schema.check_id_set_mismatch` |
| `report.result-shape` | `schema.result_shape_invalid` |
| `report.blocked-by` | `dependency.blocked_by_invalid` |
| `report.reason-code` | `schema.unknown_reason_code` |
| `report.aggregate` | `contract.aggregate_mismatch` |
| `not_evaluated` | `dependency.blocked` |
| `known.what` | `contract.known_what_mismatch` |
| `known.ccbench-pin` | `input.known_ccbench_pin_mismatch` |
| `known.selection-rules` | `contract.known_selection_rules_mismatch` |
| `known.entries` | `contract.known_entries_mismatch` |
| `known.s1b-pairing` | `contract.known_s1b_pairing_mismatch` |
| `known.reference-values-note` | `contract.known_reference_values_mismatch` |
| `known.source-records` | `contract.known_source_records_mismatch` |
| `known.source-paths` | `contract.known_source_paths_mismatch` |
| `known.source-tree-blobs` | `input.known_source_tree_blob_mismatch` |
| `known.enumeration-snapshot` | `contract.known_enumeration_snapshot_mismatch` |
| `known.final-record-count` | `contract.known_record_count_mismatch` |
| `measurement.what` | `contract.measurement_what_mismatch` |
| `measurement.known-reference` | `dependency.measurement_known_reference_mismatch` |
| `measurement.ccbench-pin` | `input.measurement_ccbench_pin_mismatch` |
| `measurement.cells` | `contract.measurement_cells_mismatch` |
| `measurement.comparisons` | `contract.measurement_comparisons_mismatch` |
| `measurement.s1b-pairing` | `contract.measurement_s1b_pairing_mismatch` |
| `measurement.operating-point` | `contract.measurement_operating_point_mismatch` |
| `measurement.workload-flags` | `contract.measurement_workload_flags_mismatch` |
| `measurement.master-seed` | `contract.measurement_master_seed_mismatch` |
| `measurement.schedule` | `contract.measurement_schedule_mismatch` |
| `measurement.schedule-hash` | `contract.measurement_schedule_hash_mismatch` |
| `measurement.observations-shape` | `schema.measurement_observations_invalid` |
| `measurement.observations-bijection` | `contract.measurement_observation_bijection_mismatch` |
| `measurement.wal-source-pointer-shape` | `schema.measurement_wal_pointer_invalid` |
| `measurement.analysis-shape` | `schema.measurement_analysis_invalid` |
| `measurement.analysis-statistics` | `output.measurement_statistic_mismatch` |
| `measurement.analysis-p-values` | `output.measurement_p_value_mismatch` |
| `measurement.analysis-gates` | `output.measurement_gate_mismatch` |
| `measurement.analysis-effects` | `output.measurement_effect_mismatch` |
| `measurement.analysis-families` | `output.measurement_family_mismatch` |
| `holdout.what` | `contract.holdout_what_mismatch` |
| `holdout.lifecycle-stage` | `contract.holdout_lifecycle_stage_mismatch` |
| `holdout.design-source` | `input.holdout_design_source_mismatch` |
| `holdout.known-reference` | `dependency.holdout_known_reference_mismatch` |
| `holdout.match-convention` | `contract.holdout_match_convention_mismatch` |
| `holdout.search-declaration` | `contract.holdout_search_declaration_mismatch` |
| `holdout.search-enumeration` | `contract.holdout_search_enumeration_mismatch` |
| `holdout.holdouts` | `contract.holdout_definition_mismatch` |
| `holdout.unknownness-snapshot` | `contract.holdout_snapshot_mismatch` |
| `holdout.positive-control` | `contract.holdout_positive_control_mismatch` |
| `holdout.derangement` | `contract.holdout_derangement_mismatch` |
| `holdout.confirmation` | `contract.holdout_confirmation_mismatch` |
| `holdout.lifecycle-fields` | `contract.holdout_lifecycle_fields_mismatch` |
| `holdout.measurement-closure` | `contract.holdout_measurement_closure_mismatch` |
| `lineage.introduction` | `lineage.introduction_invalid` |
| `lineage.generation-diff` | `lineage.generation_diff_invalid` |
| `input.generation-tree-blob` | `input.generation_tree_blob_mismatch` |
| `lineage.receipt-binding` | `lineage.receipt_binding_mismatch` |
| `authorization.approval-reference` | `authorization.approval_reference_invalid` |
| `authorization.report-hashes` | `authorization.report_hash_mismatch` |
| `authorization.bundle-digest` | `authorization.bundle_digest_mismatch` |
| `authorization.approval-topology` | `authorization.approval_topology_invalid` |
| `lineage.pointer-chain` | `lineage.pointer_chain_invalid` |
| `lineage.bundle-lockstep` | `lineage.bundle_lockstep_mismatch` |
| `authorization.revocation-state` | `authorization.bundle_revoked` |
| `authorization.cancellation-state` | `authorization.pointer_cancelled` |
| `lineage.active-unique` | `lineage.active_ambiguous` |
| `receipt.schema` | `schema.receipt_invalid` |
| `receipt.generation` | `lineage.receipt_generation_mismatch` |
| `receipt.g-hgen-binding` | `lineage.receipt_commit_mismatch` |
| `receipt.inventory` | `lineage.receipt_inventory_mismatch` |
| `receipt.predecessors` | `lineage.receipt_predecessor_mismatch` |
| `receipt.successors` | `lineage.receipt_successor_mismatch` |
| `receipt.projection` | `contract.projection_mismatch` |
| `receipt.metadata-moves` | `contract.metadata_pointer_mismatch` |
| `receipt.audit-input` | `input.wal_audit_input_mismatch` |
| `receipt.holdout-confirmation` | `contract.holdout_confirmation_mismatch` |
| `receipt.search-report-path` | `output.search_report_missing` |
| `receipt.search-report-bytes` | `output.search_report_hash_mismatch` |
| `receipt.search-report-content` | `contract.search_report_mismatch` |
| `receipt.output-tree-blobs` | `output.generation_blob_mismatch` |
| `receipt.input-tree-closure` | `input.generation_closure_mismatch` |
| `receipt.commit-topology` | `contract.receipt_commit_topology_mismatch` |
| `approval.schema` | `schema.approval_invalid` |
| `approval.filename` | `authorization.approval_filename_mismatch` |
| `approval.components` | `authorization.approval_component_mismatch` |
| `approval.report-hashes` | `authorization.report_hash_mismatch` |
| `approval.report-paths` | `output.approval_report_missing` |
| `approval.report-bytes` | `authorization.report_hash_mismatch` |
| `approval.report-subjects` | `authorization.report_subject_mismatch` |
| `approval.report-aggregate` | `authorization.report_not_pass` |
| `approval.report-validation-head` | `authorization.report_validation_head_invalid` |
| `approval.bundle-digest` | `authorization.bundle_digest_mismatch` |
| `approval.receipt-reference` | `authorization.approval_receipt_mismatch` |
| `approval.production-root-topology` | `lineage.production_root_topology_invalid` |
| `approval.manifest-root-topology` | `lineage.manifest_root_topology_invalid` |
| `approval.report-topology` | `lineage.report_topology_invalid` |
| `approval.commit-ancestry` | `authorization.approval_ancestry_invalid` |
| `approval.commit-diff` | `authorization.approval_diff_invalid` |
| `approval.commit-merge` | `authorization.approval_merge_forbidden` |
| `approval.human-trailer` | `authorization.human_trailer_invalid` |
| `approval.unique-selection` | `authorization.approval_selection_ambiguous` |
| `approval.revocation` | `authorization.bundle_revoked` |
| `pointer.schema` | `schema.pointer_invalid` |
| `pointer.filename` | `lineage.pointer_filename_mismatch` |
| `pointer.genesis` | `lineage.pointer_genesis_invalid` |
| `pointer.parent` | `lineage.pointer_parent_invalid` |
| `pointer.generation-step` | `lineage.pointer_generation_step_invalid` |
| `pointer.bundle-lockstep` | `lineage.bundle_lockstep_mismatch` |
| `pointer.receipt-reference` | `lineage.pointer_receipt_mismatch` |
| `pointer.approval-reference` | `authorization.approval_reference_invalid` |
| `pointer.no-fork` | `lineage.pointer_fork` |
| `pointer.no-gap` | `lineage.generation_gap` |
| `pointer.no-rollback` | `lineage.rollback_forbidden` |
| `pointer.revocation` | `authorization.bundle_revoked` |
| `pointer.cancellation` | `authorization.pointer_cancelled` |
| `pointer.unique-tip` | `lineage.active_ambiguous` |
| `pointer.x-commit` | `authorization.activation_topology_invalid` |
| `revocation.schema` | `schema.revocation_invalid` |
| `revocation.target` | `authorization.revocation_target_invalid` |
| `revocation.unique` | `authorization.revocation_duplicate` |
| `revocation.commit-topology` | `authorization.revocation_topology_invalid` |
| `revocation.commit-diff` | `authorization.revocation_diff_invalid` |
| `revocation.commit-merge` | `authorization.revocation_merge_forbidden` |
| `revocation.human-trailer` | `authorization.human_trailer_invalid` |
| `revocation.immutable` | `lineage.record_mutated` |
| `cancellation.schema` | `schema.cancellation_invalid` |
| `cancellation.target` | `authorization.cancellation_target_invalid` |
| `cancellation.fork-loser` | `lineage.rollback_forbidden` |
| `cancellation.unique` | `authorization.cancellation_duplicate` |
| `cancellation.commit-topology` | `authorization.cancellation_topology_invalid` |
| `cancellation.commit-diff` | `authorization.cancellation_diff_invalid` |
| `cancellation.commit-merge` | `authorization.cancellation_merge_forbidden` |
| `cancellation.human-trailer` | `authorization.human_trailer_invalid` |
| `cancellation.immutable` | `lineage.record_mutated` |
| `legacy.*-raw-root` | `output.legacy_root_mismatch` |
| `legacy.*-strict-json` | `document.json_invalid` |
| `legacy.*-type` | `schema.legacy_type_invalid` |
| `audit.input-binding` | `input.wal_audit_input_mismatch` |
| `audit.wal-blob` | `input.wal_blob_mismatch` |
| `audit.campaign-start` | `contract.wal_campaign_start_mismatch` |
| `audit.session-interval` | `contract.wal_session_interval_invalid` |
| `audit.wrapper-identity` | `contract.wal_wrapper_identity_mismatch` |
| `audit.schedule-bijection` | `contract.measurement_observation_bijection_mismatch` |
| `audit.value-origin` | `contract.measurement_value_origin_mismatch` |
| `audit.aggregate` | `authorization.wal_audit_failed` |
| `launch.argument-type` | `schema.launch_argument_invalid` |
| `launch.active-resolution` | `lineage.active_resolution_invalid` |
| `launch.enumeration-stable` | `contract.live_enumeration_changed` |
| `launch.exemptions` | `contract.live_scan_exemption_invalid` |
| `launch.expected-hits` | `contract.live_expected_hits_mismatch` |
| `launch.positive-control` | `contract.live_positive_control_failed` |
| `launch.bound-artifact-stable` | `contract.live_bound_artifact_changed` |
| `launch.aggregate` | `authorization.launch_validation_failed` |
| `prediction.schema` | `schema.prediction_invalid` |
| `prediction.body` | `contract.prediction_body_mismatch` |
| `prediction.legacy-field-absent` | `schema.prediction_legacy_field_present` |
| `prediction.semantic-closure` | `input.prediction_semantic_closure_mismatch` |
| `prediction.source-tree-blobs` | `input.prediction_source_tree_blob_mismatch` |
| `prediction.introduction` | `lineage.prediction_introduction_invalid` |
| `prediction.parent-basis` | `lineage.prediction_parent_basis_invalid` |
| `prediction.immutable` | `lineage.prediction_record_mutated` |
| `prediction.published-type` | `schema.prediction_published_type_required` |
| `prediction.bundle-generation-schema` | `schema.prediction_generation_schema_mismatch` |
| propagation freeze observation missing | `dependency.freeze_observation_missing` |
| propagation freeze observation schema | `schema.freeze_observation_invalid` |
| propagation freeze identity mismatch | `contract.freeze_identity_mismatch` |
| propagation freeze observation mismatch | `contract.freeze_observation_mismatch` |
| propagation freeze observation nonpass | `contract.freeze_observation_nonpass` |
| propagation launch observation missing | `dependency.freeze_launch_missing` |
| propagation launch observation schema | `schema.freeze_launch_invalid` |
| propagation launch observation mismatch | `contract.freeze_launch_mismatch` |
| propagation launch observation nonpass | `contract.freeze_launch_nonpass` |
| Git command failure | `environment_git.command_failed` |
| non-commit HEAD | `environment_git.head_not_commit` |
| unsupported object format | `environment_git.object_format_unsupported` |
| shallow repo | `environment_git.shallow_repository` |
| replace refs | `environment_git.replace_refs_present` |
| grafts | `environment_git.grafts_present` |
| missing object | `environment_git.object_missing` |
| unexpected object type | `environment_git.object_type_mismatch` |
| direct protected write | `authorization.direct_write_forbidden` |
| forbidden shell command | `authorization.command_forbidden` |
| generation plan mismatch | `contract.generation_plan_mismatch` |
| start snapshot mismatch | `environment_git.start_snapshot_changed` |
| output path exists | `output.generation_path_exists` |
| output path escape/type | `output.generation_path_invalid` |

### S2-4.6 literal三面とpositive fixture

literal面は次の3面に分離する。

1. production shell: `freeze_permanent_roots.py`
2. production literal data: generation-independent baseと`freeze_permanent_roots_g<N>.py`
3. test-side `FROZEN_MANIFEST` と、別file・別値源の
   `test_freeze_permanent_literal_golden.py`

positive-control fixture:

```text
path: orchestrator/tests/data/freeze_holdout_positive_control_v1.txt
root key: positive-control/rr50/v1
raw bytes:
ycsb_rratio=50\n
ycsb_zipf_skew=0.9\n
ycsb_rmw=0\n
sha256: caee6deabcf6209f5e8d59ee104a64b6bcf18a2a6054b1cefd6141709802faa7
```

fixture bytesは手書き固定で、search/builderから生成しない。direct testはfixtureだけを検索対象とし、
baselineで当該path 1 hit、検索predicate単独mutantで0 hit、revertで1 hitを要求する。fixture bytes自体を
mutateしてroot mismatchを先行させてはならない。

owner: shell/base/golden **W-a**、holdout predicate **W-c**、gN literal **W-e**。

---

## §S2-5 §7-G guard と writer CLI

### S2-5.1 generation plan

path:

```text
$(git rev-parse --git-path izanagi-freeze-generation)/<transaction_id>/plan.json
```

`transaction_id` はlowercase 32hex。planはexact 7 fields。

```text
schema_version = "freeze-bundle-generation-plan/v1"
transaction_id
generation_number
h_gen
owned_paths
start_snapshot_sha256
search_exemptions
```

owned_pathsはNから導出する3 generation path。caller指定禁止。
search exemptionsはg0..g(N-1) holdoutのexact `{path,sha256}`。

### S2-5.2 start snapshot

inventory path:

```text
$(git rev-parse --git-path izanagi-freeze-generation)/<transaction_id>/start-snapshot.json
```

exact 6 fields:

```text
schema_version = "freeze-generation-start-snapshot/v1"
superproject_commit
superproject_tree
ccbench_commit
ccbench_tree
entries
```

entryは次の二型だけである。

```json
{"repo":"superproject","path":"docs/x","mode":"100644","git_blob_oid":"<40hex>","raw_sha256":"<64hex>"}
{"repo":"superproject","path":"external/ccbench","mode":"160000","commit_oid":"<40hex>"}
```

ccbench tracked entryは`repo=="external/ccbench"`。regular/executable/symlinkは
mode `100644|100755|120000` とblob OID/raw hashを持つ。gitlinkはcommit OIDを持つ。
順序は`(repo UTF-8 bytes,path UTF-8 bytes)`。path一意。

```python
DOMAIN = b"izanagi.freeze-generation-start-snapshot/v1\x00"
start_snapshot_sha256 = sha256(DOMAIN + canonical_snapshot_bytes)
```

範囲はtracked file/symlink/gitlinkのみ。untracked fileをsnapshotで検出するとは主張しない。
各family生成前、search前後、publish前後で次を再検査する。

- superproject commit OID
- superproject tree OID
- ccbench commit OID
- ccbench tree OID
- tracked inventory bytes/mode/path

この限定に伴う受理集合の変化は§S2-12の§14追記案へ明示する。

### S2-5.3 staging/search/publish

staging:

```text
$(git rev-parse --git-path izanagi-freeze-generation)/<transaction_id>/stage/
known.json
measurement.json
holdout.json
```

directory mode 0700、file mode 0600、O_EXCL/O_NOFOLLOW。Git列挙domain外。
final pathをgeneratorへ渡さない。

generation search reportの一時正本は同transaction直下の
`generation-search-report.json` (mode 0600、O_EXCL/O_NOFOLLOW) とする。live search直後にcanonical bytesを
一度だけ書き、holdout confirmationはそのraw hashを使う。`reports --generation <N>` は、generation/H_genが
一致するcompleted planをexactly one導出し、このbytesのhashがreceipt confirmationと一致する場合だけQの
content-addressed pathへ同一bytesをpublishする。reportを後から現在のworktree searchで再生成しない。

searchは現行のroot tracked regular、root untracked regular、ccbench tracked regular列挙を維持する。
broad prefix exclusionを禁止し、planのexact path/hash exemptionsだけを免除する。
exempt fileもenumeration/file_countには残す。staging/plan pathが列挙へ現れたら拒否する。

順序:

```text
prepare/snapshot
→ known stage
→ measurement stage
→ generation live search
→ confirmed_by/confirmed_at
→ holdout stage
→ candidate三型verify
→ O_EXCL publish
→ tracked snapshot delta verify
→ G
```

publish後の許可deltaはowned path 3件の通常file追加だけ。

### S2-5.4 writer CLI

保護namespaceを変更できるCLIは一つだけである。

```text
orchestrator/campaign/freeze_permanent_cli.py
```

| subcommand | exact write argv | write path | post-commit gate |
|---|---|---|---|
| `generate` bundle | `generate --generation <N> --confirmed-by <NAME> --confirmed-at <UTC>` | generation 3 path | G parent=H_gen、3 Aのみ |
| `generate` prediction | `generate --prediction-evidence-id <32hex>` | `output/s8b-freeze/selector_predictions.json` | G_pred、1 Aのみ、§S2-6 |
| `pointer-init` | `pointer-init` | g0 exact path | P0、1 Aのみ、bytes exact |
| `receipt` | `receipt --generation <N>` | g1/future receipt path | R parent=G、1 Aのみ |
| `reports` | `reports --generation <N>` | §S2-1.5/2b.4のcontent-addressed report 4 path | Q parent=L_manifest、4 Aのみ、各filename/raw hash/content再検査 |
| `approval-record` | `approval-record --generation <N> --approver <NAME> --approved-at <UTC>` + U-A1 delta | approval hash path | A、1 Aのみ、人間trailer |
| `activate` | `activate --approval-sha256 <64hex>` | active pointer hash path | X parent=selected A、1 Aのみ |
| `revoke` | `revoke --bundle-digest <64hex> --revoked-by <NAME> --revoked-at <UTC> --reason <TEXT>` | revocation path | RV exact topology |
| `cancel` | `cancel --pointer-sha256 <64hex> --cancelled-by <NAME> --cancelled-at <UTC> --reason <TEXT>` | cancellation path | CX exact topology |

`--output`, `--root`, `--staging`, arbitrary owned path、stdin script、inline Pythonを禁止する。
CLIはrepo rootを自身のlocationから導出する。全writeはparent componentのsymlink拒否、
root escape拒否、O_CREAT|O_EXCL|O_NOFOLLOW、mode 0644。

W-b/W-c/W-d moduleへのdispatchはCLIに予め固定し、後続waveがCLIへ新しい任意path escapeを追加しない。
W-e/W-fはwriter実装を変更せずCLIを実行する。

### S2-5.5 hooks

protected tree:

```text
output/s1-freeze/
output/s8b-freeze/
output/freeze-migrations/
output/freeze-permanent/
```

Write/Edit/MultiEdit/NotebookEditは常に拒否。Bash経由のcp/mv/rm/sed/tee/redirection、tree destructionを
拒否する。S2-5.4のexact CLI argvだけを許可する。hookは認証・correctness proofではなく、CLIと
post-commit verifierがauthoritative gateである。

実物根拠: `hooks/guard_write.py`、`guard_bash.py`、`hooks/README.md`。  
owner: hook **W-0**、CLI **W-c**、family modules **W-b/W-c/W-d**。

---

## §S2-6 `prediction_basis_tree` — `pre_oracle_head` 後継

prediction schemaは`8b-selector-prediction-freeze/v2`。top-level exact 11 fields。

```text
schema_version
generated_at
prediction_basis_tree
sources
selector_basis_sha256
execution_policy
static_default
derangement
rows
swapped_follow_expectations
body_sha256
```

`pre_oracle_head`は禁止する。

`prediction_basis_tree` は exact 3 fields。

```text
schema_version = "8b-prediction-basis-tree/v1"
semantic_input_closure
provenance_unverified
```

`semantic_input_closure` はGであり、exact 4 fields。

```text
schema_version = "8b-prediction-semantic-input-closure/v1"
records
record_count
records_sha256
```

recordsは `{role,path,mode,sha256}`、role/path昇順・一意。exact集合は次のunionから導出する。

- `sources` の5件: holdout_freeze/builder/role/input_schema/output_schema
- journal claimの全`payload_path`
- journal invocationの全`raw_response_path`
- journal自身

evidence path template:

```text
output/campaigns/8b-selector-prediction-<32hex>/
  journal.jsonl
  payloads/<target_holdout>-<arm>.json
  raw/<target_holdout>-<arm>.txt
```

全recordをG_predの親`H_pred=G_pred^` tree blobとして照合する。

`provenance_unverified` はMであり、exact
`{git_object_format,tree_oid,entry_count,manifest_sha256}`。
全tree manifestの値は再構成predicate、candidate acceptance、published acceptanceに使用しない。
checkerや無関係fileの変更をGへ逆流させない。

生成:

1. evidenceを上記tracked pathへG_predより前に確定。
2. HEAD commit/treeを一度捕捉。
3. semantic closure全件をtree blobと照合。
4. predictionをO_EXCL write。
5. G_predはprediction 1file追加のみ。
6. published verifierはG_predをH_v reachable historyから一意導出し、H_pred treeに対してclosureを再照合。

導入後不変性:

- G_pred後のM/D/R/C/T、mode change、delete/re-addを全拒否。
- current blobはG_pred introduction blobと一致。
- candidate verifierとpublished verifierを分離し、official consumerはpublished typed objectのみ受理。

このfieldは閲覧時系列を証明しない。「HARKingを機械排除」と主張してはならない。oracle情報を見ない生成順は
launch/runbookの運用規律であり、tree fieldとは別である。

g0/v1、g1+/v2の切替は§S2-3.5のpointer generation分岐のみ。

commit identityから宣言semantic content同値へ交換する点は受理集合を広げるため、§S2-12の§14追記案を
交換条件とする。

実物根拠: `s8b_selector_freeze.py` の現行11 fields、sources 5件、runner journal/raw response、
`pre_oracle_head`の形式+commit存在検査だけという現状。  
owner: **W-d**。

---

## §S2-7 source closure 宣言

known v2 `/source_closure` は exact 3 fields。

```text
schema_version = "s1-known-source-closure/v1"
records
file_enumerations
```

records elementは exact `{record_type,path,sha256,key}`。

record type:

```text
implementation_dependency
campaign_lock
enumeration_classifier
```

`records` はpathのUTF-8 bytes昇順、path一意。各型の`key`は次で固定し、別値や空stringを拒否する。

| `record_type` | 対象 | exact `key` |
|---|---|---|
| `implementation_dependency` | `pipeline.py` | `variant_id` |
| `implementation_dependency` | `model.py` | `Genome;Genome.__post_init__;Genome.canonical` |
| `implementation_dependency` | `source_digest.py` | `STOCK` |
| `campaign_lock` | 下記unionのcampaign.lock | `/search_config` |
| `enumeration_classifier` | sort provenance member | `/trial` |

implementation dependency初期集合:

| path | key |
|---|---|
| `orchestrator/campaign/pipeline.py` | `variant_id` |
| `orchestrator/campaign/model.py` | `Genome;Genome.__post_init__;Genome.canonical` |
| `orchestrator/campaign/source_digest.py` | `STOCK` |

file_enumerationsはexact 8件。

| ID | pattern |
|---|---|
| `p2_2_wal/balanced` | `output/campaigns/p2-2-silo-balanced-enumerate-*/runs/wal.jsonl` |
| `p2_2_wal/write-heavy` | `output/campaigns/p2-2-silo-write-heavy-enumerate-*/runs/wal.jsonl` |
| `p2_2_wal/read-heavy` | `output/campaigns/p2-2-silo-read-heavy-enumerate-*/runs/wal.jsonl` |
| `backoff_wal/balanced` | `output/campaigns/backoff-sweep-silo-balanced-sweep-*/runs/wal.jsonl` |
| `backoff_wal/write-heavy` | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-*/runs/wal.jsonl` |
| `backoff_wal/read-heavy` | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-*/runs/wal.jsonl` |
| `sort_remeasure_provenance/balanced` | `output/campaigns/p3-s6-sort-sweep-balanced-sweep-*/reports/s6_sort_sweep_provenance.json` |
| `sort_remeasure_provenance/write-heavy` | `output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-*/reports/s6_sort_sweep_provenance.json` |

各enumerationはexact
`{enumeration_id,algorithm,pattern,members,file_count}`、
`algorithm=="git-tree-glob/v1"`。配列順は上表の8 ID順で固定する。

`git-tree-glob/v1` は `H_gen` superproject treeのmode `100644|100755` leaf path全件を対象とし、patternの
`*` を「`/` を含まない0文字以上のUTF-8 byte列」へ写した**path全体一致**である。directory、symlink、
gitlink、worktree `Path.glob()` を列挙入力にしない。

membersはpath UTF-8 bytes昇順・path一意のexact `{path,disposition}`。`file_count` はboolでない
non-negative integerで `len(members)` と一致する。上表8 enumerationは各1 member以上。

p2/backoff disposition:

```text
included
screening-excluded
```

sort disposition:

```text
trial-mismatch
missing-wal
screening-excluded
eligible-remeasure
```

各p2/backoff memberのsibling `campaign.lock` を必須とし、strict JSON objectとして読む。
`/search_config` はobject必須で、そのkey集合に`screening`が**存在**すれば `screening-excluded`、
存在しなければ`included`。値のtruthinessを見ない。各enumerationは`included`を1件以上持つ。

sort dispositionは次の優先順でexactに一つを選ぶ。

1. provenance `/trial` がstringで `p3-s6-sort-sweep-remeasure` prefixでなければ `trial-mismatch`。
2. prefix一致かつsibling `runs/wal.jsonl` がH_gen treeになければ `missing-wal`。
3. WALがあり、campaign.lock `/search_config` に`screening` keyがあれば `screening-excluded`。
4. それ以外は `eligible-remeasure`。

先に一致したdispositionを採り、後段で上書きしない。sort balanced/write-heavyはそれぞれ
`eligible-remeasure` exactly 1。

records path集合は次のunionと完全一致する。

1. implementation dependency 3 path
2. p2/backoff全member対応campaign.lock
3. sortのtrial prefix一致かつWAL存在memberのcampaign.lock
4. sort全provenance member

unionの型/key対応は、1が上表の`implementation_dependency`、2/3が
`campaign_lock` + `key="/search_config"`、4が`enumeration_classifier` + `key="/trial"`。
同じpathが複数集合に現れた場合はset union後に型/keyが一意に定まらなければ拒否する。各sha256は
`H_gen:path` raw blobから再導出する。

世代遷移ではこの`records` array全体を上記unionから再導出し、順序・一意性・型・key・hashを含め
完全一致する場合だけ§S2-1.12の全体置換を許す。

record総数、member総数はH_genから生成時に確定する。

static verifyは既存source recordとsource_closure全件をH_gen tree blobへ照合する。
ccbench recordはH_genの`external/ccbench` gitlink
`d706650cdb31e442bef45b9b4216951d4fb40969`からsubmodule treeを二段解決する。
current worktree照合はG guardにのみ置き、official static acceptanceへ戻さない。

2026-07-22観測値は既存source record 63、unique path 31、24 record/6 implementation file、
8 enumeration/12 members/10 campaign.lock。これらはschema count literalではない。

実物根拠: `s1_known_axes_freeze.py`、legacy known artifact、H_gen gitlink。  
owner: **W-b**。

---

## §S2-8 §9再列挙とW-0..W-f所有表

2026-07-22再計数:

```text
grep和集合                         44 production/test file
既存 source records               63 / 31 unique path
implementation records            24 / 6 file
cells/comparisons/observations     18 / 12 / 288
legacy inventory                  9 blob
transition allowlist              13 / 9 pointer
FROZEN_MANIFEST                   8 keys
既存 required nodes              12
```

### S2-8.1 exact ownership

```text
W-0  hooks/guard_write.py
W-0  hooks/guard_bash.py
W-0  hooks/README.md
W-0  orchestrator/tests/test_hooks.py
W-0  tools/task_runs/ledger.py
W-0  orchestrator/tests/test_task_run_ledger.py
W-0  orchestrator/tests/data/freeze_nodes/w0.json

W-a  orchestrator/campaign/freeze_permanent_io.py
W-a  orchestrator/campaign/freeze_permanent_stats.py
W-a  orchestrator/campaign/freeze_permanent_roots.py
W-a  orchestrator/campaign/freeze_permanent_roots_base.py
W-a  orchestrator/tests/test_freeze_permanent_io.py
W-a  orchestrator/tests/test_freeze_permanent_stats.py
W-a  orchestrator/tests/test_freeze_permanent_literal_golden.py
W-a  orchestrator/tests/conftest.py
W-a  orchestrator/tests/data/freeze_holdout_positive_control_v1.txt
W-a  orchestrator/tests/data/freeze_nodes/base.json
W-a  orchestrator/tests/data/freeze_nodes/wa.json

W-b  orchestrator/campaign/s1_known_axes_freeze_v2.py
W-b  orchestrator/campaign/s1_measurement_freeze_v3.py
W-b  orchestrator/tests/test_s1_known_axes_freeze_v2.py
W-b  orchestrator/tests/test_s1_measurement_freeze_v3.py
W-b  orchestrator/tests/data/freeze_nodes/wb.json

W-c  orchestrator/campaign/s8b_holdout_freeze_v3.py
W-c  orchestrator/campaign/freeze_permanent_lineage.py
W-c  orchestrator/campaign/freeze_bundle_resolver.py
W-c  orchestrator/campaign/freeze_permanent_cli.py
W-c  orchestrator/tests/test_s8b_holdout_freeze_v3.py
W-c  orchestrator/tests/test_freeze_permanent_lineage.py
W-c  orchestrator/tests/test_freeze_bundle_resolver.py
W-c  orchestrator/tests/test_freeze_permanent_cli.py
W-c  orchestrator/tests/data/freeze_nodes/wc.json
W-c  output/freeze-permanent/active/746fcafabaaef09f11bc945dafc63eb177c94df5c1fb2735aadb230be2260e4b.json

W-d  orchestrator/campaign/freeze_bundle_launch.py
W-d  orchestrator/campaign/s1_direct_comparison.py
W-d  orchestrator/campaign/s1_report.py
W-d  orchestrator/campaign/s1_verify_extime_calibration.py
W-d  orchestrator/campaign/s8b_approved.py
W-d  orchestrator/campaign/s8b_freeze_io.py
W-d  orchestrator/campaign/s8b_floor_contract.py
W-d  orchestrator/campaign/s8b_floor_campaign.py
W-d  orchestrator/campaign/s8b_launch_cert.py
W-d  orchestrator/campaign/s8b_oracle_driver.py
W-d  orchestrator/campaign/s8b_oracle_manifest.py
W-d  orchestrator/campaign/s8b_selector_freeze.py
W-d  orchestrator/campaign/s8b_prediction_runner.py
W-d  orchestrator/campaign/s8b_verdict.py
W-d  orchestrator/campaign/s8b_budget.py
W-d  orchestrator/campaign/s8b_run_marker.py
W-d  orchestrator/campaign/s8b_oracle_artifacts.py
W-d  orchestrator/campaign/s8b_oracle_report.py
W-d  orchestrator/campaign/s8b_oracle_judge.py
W-d  orchestrator/campaign/s8b_materialization.py
W-d  orchestrator/tests/test_s1_direct_comparison.py
W-d  orchestrator/tests/test_s1_report.py
W-d  orchestrator/tests/test_s1_verify_extime_calibration.py
W-d  orchestrator/tests/test_s8b_approved.py
W-d  orchestrator/tests/test_s8b_freeze_io.py
W-d  orchestrator/tests/test_s8b_floor_contract.py
W-d  orchestrator/tests/test_s8b_floor_campaign.py
W-d  orchestrator/tests/test_s8b_launch_cert.py
W-d  orchestrator/tests/test_s8b_oracle_driver.py
W-d  orchestrator/tests/test_s8b_oracle_manifest.py
W-d  orchestrator/tests/test_s8b_selector_freeze.py
W-d  orchestrator/tests/test_s8b_prediction_runner.py
W-d  orchestrator/tests/test_s8b_verdict.py
W-d  orchestrator/tests/test_s8b_budget.py
W-d  orchestrator/tests/test_s8b_oracle_artifacts.py
W-d  orchestrator/tests/test_s8b_oracle_report.py
W-d  orchestrator/tests/test_s8b_oracle_judge.py
W-d  orchestrator/tests/test_s8b_materialization.py
W-d  orchestrator/tests/test_s8b_protocol_builder.py
W-d  orchestrator/tests/test_s8b_selector_input.py
W-d  orchestrator/tests/test_s8b_binding_driftguards.py
W-d  orchestrator/tests/test_real_repo_serialization.py
W-d  orchestrator/tests/test_freeze_bundle_launch.py
W-d  orchestrator/tests/test_freeze_consumer_cutover.py
W-d  orchestrator/tests/test_freeze_observation_propagation.py
W-d  orchestrator/tests/data/freeze_nodes/wd.json

W-e  orchestrator/campaign/freeze_permanent_roots_g1.py
W-e  orchestrator/tests/test_frozen_artifacts.py
W-e  orchestrator/tests/data/freeze_nodes/we.json
W-e  output/s1-freeze/known_axes_freeze.v2.g1.json
W-e  output/s1-freeze/measurement_freeze.v3.g1.json
W-e  output/s8b-freeze/holdout_freeze.v3.g1.json
W-e  output/freeze-migrations/legacy-to-permanent-g1.receipt.json
W-e  output/freeze-permanent/reports/<report_type>-<raw_sha256>.json
W-e  output/freeze-permanent/approvals/<approval_raw_sha256>.json

W-f  orchestrator/tests/README.md
W-f  docs/phase3.md
W-f  docs/worklog.md
W-f  docs/decisions.md
W-f  output/freeze-permanent/active/<g1_pointer_raw_sha256>.json
```

operational path templates:

```text
output/freeze-permanent/revocations/<bundle_digest>.json
output/freeze-permanent/active-cancellations/<pointer_sha256>.json
output/freeze-permanent/reports/<report_type>-<raw_sha256>.json
output/freeze-migrations/permanent-g<N-1>-to-g<N>.receipt.json
output/s1-freeze/known_axes_freeze.v2.g<N>.json
output/s1-freeze/measurement_freeze.v3.g<N>.json
output/s8b-freeze/holdout_freeze.v3.g<N>.json
output/env/<env_tag>/calibration/s1_verify_extime.v2.g<N>.json
output/reports/s1_direct_comparison/report.v2.g<N>.json
output/campaigns/8b-selector-prediction-<32hex>/**
output/s8b-freeze/selector_predictions.json
```

これらのwriterは§S2-5のCLIまたはW-dの明示consumer/output contractだけである。

### S2-8.2 W-d consumer registry

production consumerは次の19件で固定する。

```text
orchestrator/campaign/s1_direct_comparison.py
orchestrator/campaign/s1_report.py
orchestrator/campaign/s1_verify_extime_calibration.py
orchestrator/campaign/s8b_approved.py
orchestrator/campaign/s8b_freeze_io.py
orchestrator/campaign/s8b_floor_contract.py
orchestrator/campaign/s8b_floor_campaign.py
orchestrator/campaign/s8b_launch_cert.py
orchestrator/campaign/s8b_oracle_driver.py
orchestrator/campaign/s8b_oracle_manifest.py
orchestrator/campaign/s8b_selector_freeze.py
orchestrator/campaign/s8b_prediction_runner.py
orchestrator/campaign/s8b_verdict.py
orchestrator/campaign/s8b_budget.py
orchestrator/campaign/s8b_run_marker.py
orchestrator/campaign/s8b_oracle_artifacts.py
orchestrator/campaign/s8b_oracle_report.py
orchestrator/campaign/s8b_oracle_judge.py
orchestrator/campaign/s8b_materialization.py
```

各入口の先行predicate順はW-d開始時に再実測して確定する許可holeである。決定権者はW-d親。
registryの19件集合自体はholeではなく固定する。1件でも旧family path直読が残ればW-d不合格。

`test_freeze_bundle_resolver.py` はW-c所有のresolver単体testであり、fixture上のresolve-once、family混在拒否、
typed returnだけを検査する。19 production fileのsource直読禁止は検査しない。後者はW-d所有の
`test_freeze_consumer_cutover.py::test_all_registered_consumers_reject_direct_family_reads` が上記literal集合を
全件走査する。この所有境界を跨いでW-c時点に現行consumer cutoverを要求しない。

### S2-8.3 node manifest

現行repoに `REQUIRED_FREEZE_NODES` は存在しない。本設計で新設する。W-aで`conftest.py`を一回だけ、
次のexact 7 filenameをclosed setとする reader へ変更し、以後conftestは変更しない。reader は
**7 filename のうち実在する file のみ**を読む — 存在しない file は「所有 wave が未 land」として
許容する (wave 単独 green の条件。7/7 の実在と final union の完全性は下記の W-f final check が
X の前提として検査するため、missing が X まで黙って残ることはない)。

```text
orchestrator/tests/data/freeze_nodes/base.json
orchestrator/tests/data/freeze_nodes/w0.json
orchestrator/tests/data/freeze_nodes/wa.json
orchestrator/tests/data/freeze_nodes/wb.json
orchestrator/tests/data/freeze_nodes/wc.json
orchestrator/tests/data/freeze_nodes/wd.json
orchestrator/tests/data/freeze_nodes/we.json
```

各data fileはexact 3 keysのstrict JSON objectである。

```json
{
  "schema_version": "freeze-required-nodes/v1",
  "wave": "base",
  "nodes": ["test_file.py::test_function"]
}
```

- filename→`wave` はexact `base→base,w0→W-0,wa→W-a,wb→W-b,wc→W-c,wd→W-d,we→W-e`。
- `nodes` はUTF-8 bytes昇順のstring array。各値はregex
  `^test_[a-z0-9_]+\.py::test_[a-z0-9_]+$`、file内/7 file間で一意。class node、parameter suffix、
  path componentを拒否する。
- 未知filename、未知key、duplicate node (実在file間)、空array、未収集nodeを拒否する (空array は
  実在するfileについての拒否 — 後続waveのfileを空placeholderとして先行導入することを禁止する。
  各waveの受入は「自waveのfileが実在し、自waveの全detector nodeを含む」ことを条件に含める)。
- **final check** (`test_frozen_artifacts.py::test_required_freeze_nodes_final_manifest_is_complete`、
  **実装と file 所有は W-e** — 42 node は W-e land 時点で全 7 file が実在し union が成立するため
  W-e の受入で緑になる。**X の前提検査として W-f の受入全走にも含まれる** — W-f はこの check を
  実行するだけでコードを所有しない): 7 file全実在 + 和集合が下記final literal 42 nodeと完全一致する
  ことを検査する。実在fileのみ読むreader構造がXまで「黙ってskip」で残ることをこのcheckが構造的に
  塞ぐ。この node 自身は 42 node manifest の外 (wf 用 data file は設けない — 検査対象の manifest に
  検査者自身を入れない)。final check 自体を消す変更への機械 anchor は無く、第 1 段 §10/§14 の
  既受諾限界 (manifest 系の変更は A 型レビュー対象という運用規律) と同型で受ける。

final literalは次の **42 node** (既存実在12 + 新規detector 29 + collectability meta-test 1) の
完全和集合である。既存12は2026-07-22 HEADの関数定義を実測した値で、生成器から導出しない。

`base.json` — 既存12:

```text
test_frozen_artifacts.py::test_frozen_artifacts_match_manifest
test_frozen_artifacts.py::test_manifest_shape_is_exact
test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes
test_s1_stats.py::test_effect_sizes_use_registered_definitions
test_s1_stats.py::test_p_star_and_family_p
test_s1_stats.py::test_three_fixed_distributions_match_independent_enumeration
test_s8b_ratified_freeze.py::test_approval_commit_with_extra_file_rejected
test_s8b_ratified_freeze.py::test_generation_and_approval_same_commit_rejected
test_s8b_ratified_freeze.py::test_non_ancestry_user_commit_rejected
test_s8b_ratified_freeze.py::test_pointer_fork_and_cancellation_recovery
test_s8b_ratified_freeze.py::test_root_bytes_scan_rejects_a_leaked_root
test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control
```

`w0.json` — 新規3:

```text
test_hooks.py::test_bash_direct_writes_denied
test_hooks.py::test_s8b_freeze_namespace_denied
test_task_run_ledger.py::test_evidence_namespace_root_is_rejected
```

`wa.json` — 新規7:

```text
test_freeze_permanent_io.py::test_check_registry_is_closed_world_for_every_schema
test_freeze_permanent_io.py::test_nonpass_result_forces_aggregate_failure
test_freeze_permanent_io.py::test_not_evaluated_blocked_by_is_existing_unique_and_strictly_earlier
test_freeze_permanent_literal_golden.py::test_literal_keysets_and_required_check_ids_match_independent_golden
test_freeze_permanent_literal_golden.py::test_three_literal_surfaces_have_independent_value_sources
test_freeze_permanent_stats.py::test_conformance_vectors_match_external_literals
test_freeze_permanent_stats.py::test_producer_and_verifier_import_graphs_are_disjoint
```

`wb.json` — 新規5:

```text
test_s1_known_axes_freeze_v2.py::test_generation_transition_rederives_dynamic_source_subtrees
test_s1_known_axes_freeze_v2.py::test_source_closure_uses_h_gen_tree_blobs
test_s1_measurement_freeze_v3.py::test_analysis_results_match_independent_reference_for_all_twelve_comparisons
test_s1_measurement_freeze_v3.py::test_observations_are_schedule_bijection_with_canonical_float_hex
test_s1_measurement_freeze_v3.py::test_wal_source_audit_uses_h_gen_tree_blobs_and_nonoverlapping_sessions
```

`wc.json` — 新規7:

```text
test_freeze_bundle_resolver.py::test_bundle_is_resolved_once_without_family_mixing
test_freeze_permanent_cli.py::test_each_writer_has_fixed_argv_path_o_excl_and_post_commit_gate
test_freeze_permanent_lineage.py::test_approval_pointer_fork_gap_rollback_and_report_hashes
test_freeze_permanent_lineage.py::test_cancellation_topology_is_exact
test_freeze_permanent_lineage.py::test_receipt_rederives_g_h_gen_and_all_input_blobs
test_freeze_permanent_lineage.py::test_revocation_topology_is_exact
test_s8b_holdout_freeze_v3.py::test_external_positive_control_baseline_mutant_revert
```

`wd.json` — 新規6:

```text
test_freeze_bundle_launch.py::test_lifecycle_expected_hits_are_exact
test_freeze_bundle_launch.py::test_live_scan_is_mandatory_and_report_hash_is_actual
test_freeze_consumer_cutover.py::test_all_registered_consumers_reject_direct_family_reads
test_freeze_observation_propagation.py::test_identity_static_and_launch_observations_survive_all_hops
test_s8b_selector_freeze.py::test_v2_published_type_is_immutable_after_introduction
test_s8b_selector_freeze.py::test_v2_published_verifier_binds_semantic_prediction_basis
```

`we.json` — 新規detector 1 + meta-test 1:

```text
test_frozen_artifacts.py::test_g1_observations_match_h_gen_wal_blobs
test_frozen_artifacts.py::test_required_freeze_nodes_are_collectable_exactly_once
```

meta-testはこの42件がcollection結果にそれぞれexactly once存在することと、manifest自身のunionが上記
literalと一致することを検査する。production registry/predicate/data manifestの同時削除はW-aの独立
golden nodeが捕捉し、meta-testだけへ自己依存させない。

全新設testは自走harnessを持ち、pytest-only allowlistへ追加しない。
`orchestrator/tests/README.md` はW-fで一度だけこの事実を記録する。

`freeze-migrations` / `freeze-permanent` は
`tools/task_runs/ledger.py` の禁止output namespaceへW-0で追加する。

---

## §S2-9 変異テスト事前登録候補

### S2-9.1 状態

- `candidate`: 本書で仕様変異点、第一失敗check、detector nodeを定めた状態。B-057確定登録ではない。
- `confirmed`: 実装wave開始時に親が実コードを読み、baseline pass、mutant fail、revert pass、
  第一失敗checkの単独性を確認してB-057へ登録した状態。

先行predicateにmaskされる場合はcandidateをそのままconfirmedにしてはならない。fixtureまたは変異点を
再照準する。揮発する例外文字列、時刻、temp path、診断payloadを期待値へ焼き込まない。

### S2-9.2 candidates

| ID | 変異 | 第一失敗check | detector |
|---|---|---|---|
| M0-write | freeze namespace 1件をWrite拒否から除外 | protected write | `test_hooks.py::test_s8b_freeze_namespace_denied` |
| M0-bash | direct shell write判定を除外 | protected command | `test_hooks.py::test_bash_direct_writes_denied` |
| M0-ledger |禁止namespace 1件を削除 | ledger namespace | `test_task_run_ledger.py::test_evidence_namespace_root_is_rejected` |
| Ma-registry | unknown/missing/duplicate IDを受理 | `report.exact-id-set` | `test_freeze_permanent_io.py::test_check_registry_is_closed_world_for_every_schema` |
| Ma-registry-coupled | production registry ID・対応predicate・freeze_nodes data entryを同時削除 | `report.exact-id-set` (独立goldenとの不一致) | `test_freeze_permanent_literal_golden.py::test_literal_keysets_and_required_check_ids_match_independent_golden` |
| Ma-blocked | missing/later/pass IDをblocked_byへ許可 | `report.blocked-by` | `test_freeze_permanent_io.py::test_not_evaluated_blocked_by_is_existing_unique_and_strictly_earlier` |
| Ma-aggregate | error/not_evaluated 1件でもpass aggregate | `report.aggregate` | `test_freeze_permanent_io.py::test_nonpass_result_forces_aggregate_failure` |
| Ma-stat-ref |独立側greater tailを`>`へ変更 | conformance literal | `test_freeze_permanent_stats.py::test_conformance_vectors_match_external_literals` |
| Ma-import | producer/verifier importを共有 | import separation | `test_freeze_permanent_stats.py::test_producer_and_verifier_import_graphs_are_disjoint` |
| Ma-literal | production/test/goldenを同値源から導出 | literal independence | `test_freeze_permanent_literal_golden.py::test_three_literal_surfaces_have_independent_value_sources` |
| Mb-known-tree | H_gen blob照合をworktreeへ変更 | `known.source-tree-blobs` | `test_s1_known_axes_freeze_v2.py::test_source_closure_uses_h_gen_tree_blobs` |
| Mb-known-dynamic | member/path変化を禁止または任意許可 | `known.enumeration-snapshot` | `test_s1_known_axes_freeze_v2.py::test_generation_transition_rederives_dynamic_source_subtrees` |
| Mb-observation | cell/schedule全単射を削除 | `measurement.observations-bijection` | `test_s1_measurement_freeze_v3.py::test_observations_are_schedule_bijection_with_canonical_float_hex` |
| Mb-stat-prod | family maxをminへ変更 | `measurement.analysis-families` | `test_s1_measurement_freeze_v3.py::test_analysis_results_match_independent_reference_for_all_twelve_comparisons` |
| Mb-wal-basis | WALをH_v/worktreeから読む | `audit.wal-blob` | `test_s1_measurement_freeze_v3.py::test_wal_source_audit_uses_h_gen_tree_blobs_and_nonoverlapping_sessions` |
| Mb-session | session overlap/複数commitを許可 | `audit.session-interval` | 同上 |
| Mc-positive |固定fixtureを認識するpredicateを無効化 | `holdout.positive-control` | `test_s8b_holdout_freeze_v3.py::test_external_positive_control_baseline_mutant_revert` |
| Mc-receipt | G^/H_genまたはG diffを緩和 | `receipt.g-hgen-binding` | `test_freeze_permanent_lineage.py::test_receipt_rederives_g_h_gen_and_all_input_blobs` |
| Mc-order | digest component順を無視 | `approval.components` | `test_freeze_permanent_lineage.py::test_approval_pointer_fork_gap_rollback_and_report_hashes` |
| Mc-domain | digest domain separatorを変更 | `approval.bundle-digest` | 同上 |
| Mc-report-schema | approvalのreport hash fieldを欠落/別型にする | `approval.schema` | 同上 |
| Mc-report-semantic | approval/filenameの64hexは維持し、導出pathのtracked report raw bytesだけを別canonical本文へ置換 | `approval.report-bytes` | 同上 |
| Mc-resolve-once | familyを個別再読 | resolver call-count | `test_freeze_bundle_resolver.py::test_bundle_is_resolved_once_without_family_mixing` |
| Mc-cli | arbitrary output/pathまたは上書きを許可 | CLI/O_EXCL | `test_freeze_permanent_cli.py::test_each_writer_has_fixed_argv_path_o_excl_and_post_commit_gate` |
| Mc-rv-diff | revocation commitへ余剰fileを追加 | `revocation.commit-diff` | `test_freeze_permanent_lineage.py::test_revocation_topology_is_exact` |
| Mc-rv-merge | revocation introductionをmerge commitにする | `revocation.commit-merge` | 同上 |
| Mc-rv-trailer | revocationの`AI-Agent: none`を変更/欠落 | `revocation.human-trailer` | 同上 |
| Mc-cx-diff | cancellation commitへ余剰fileを追加 | `cancellation.commit-diff` | `test_freeze_permanent_lineage.py::test_cancellation_topology_is_exact` |
| Mc-cx-merge | cancellation introductionをmerge commitにする | `cancellation.commit-merge` | 同上 |
| Mc-cx-trailer | cancellationの`AI-Agent: none`を変更/欠落 | `cancellation.human-trailer` | 同上 |
| Md-s1-cutover | S-1 consumerを旧path直読へ戻す | consumer registry | `test_freeze_consumer_cutover.py::test_all_registered_consumers_reject_direct_family_reads` |
| Md-8b-cutover | 8b consumerを旧path直読へ戻す | consumer registry | 同上 |
| Md-live-scan | launch live scanを省略 | `launch.expected-hits` | `test_freeze_bundle_launch.py::test_live_scan_is_mandatory_and_report_hash_is_actual` |
| Md-live-lifecycle | lifecycle別expected hitを共通化 | `launch.expected-hits` | `test_freeze_bundle_launch.py::test_lifecycle_expected_hits_are_exact` |
| Md-propagation | identity/static/launch observation 1 hopを削除 | propagation contract | `test_freeze_observation_propagation.py::test_identity_static_and_launch_observations_survive_all_hops` |
| Md-basis-coupled | semantic closure hashとH_pred blob照合を同時削除 | prediction basis | `test_s8b_selector_freeze.py::test_v2_published_verifier_binds_semantic_prediction_basis` |
| Md-published-type | candidate/raw dictをofficialで許可 | `prediction.published-type` | `test_s8b_selector_freeze.py::test_v2_published_type_is_immutable_after_introduction` |
| Md-prediction-mutable | G_pred後のM/D/R/C/Tを許可 | `prediction.immutable` | 同上 |
| Md-schema-split | g1+でprediction v1を受理 | `prediction.bundle-generation-schema` | 同上 |
| Me-g-extra-diff | valid Gへ無関係file追加を許可 | `receipt.commit-topology` | `test_freeze_permanent_lineage.py::test_receipt_rederives_g_h_gen_and_all_input_blobs` |
| Me-audit | WAL audit failでもA作成 | `audit.aggregate` | `test_frozen_artifacts.py::test_g1_observations_match_h_gen_wal_blobs` |
| Me-keyset | len 12だけで旧8∪新4を検査しない | independent golden keyset | `test_freeze_permanent_literal_golden.py::test_literal_keysets_and_required_check_ids_match_independent_golden` |
| Me-root-pair | production/test rootを同じ誤値へ同時変更 | receipt successor | `test_freeze_permanent_literal_golden.py::test_three_literal_surfaces_have_independent_value_sources` |
| Me-A-diff | A commitへapproval以外の余剰fileを追加 | `approval.commit-diff` | `test_freeze_permanent_lineage.py::test_approval_pointer_fork_gap_rollback_and_report_hashes` |
| Me-A-merge | A introductionをmerge commitにする | `approval.commit-merge` | 同上 |
| Me-A-trailer | Aの`AI-Agent: none`を変更/欠落 | `approval.human-trailer` | 同上 |
| Mf-X-parent | X^をselected Aの任意descendantへ緩和 | `pointer.x-commit` | 同上 |
| Mf-X-diff | Xへpointer外変更を許可 | `pointer.x-commit` | 同上 |
| Mf-active-observation | non-pass observationで実走 | `launch.aggregate` | `test_freeze_observation_propagation.py::test_identity_static_and_launch_observations_survive_all_hops` |

cycle単独変異と既存path M-status変異は等価変異のため登録しない。expiry変異はU-A1裁定まで候補化しない。
同じdetector nodeを共有する行もfixtureは行ごとに独立させ、1 fixtureへdiff/merge/trailer等を束ねない。
confirmed化では表の第一失敗checkだけが最初のnonpassであり、他の変異理由が同fixtureにないことを検査する。

---

## §S2-10 launch 層契約

static active型から実走型への唯一の変換:

```text
launch_validate(
    ActiveOfficialLegacyBundle | ActiveOfficialBundle
) -> LaunchValidatedOfficialBundle
```

返却型は exact fieldsを持つdeep-immutable object。

```text
active_bundle
validation_head
freeze_identity
verification_observation
live_scan_report
live_scan_report_sha256
```

skip flag、生dict、family別引数を禁止する。19 consumerの全実走入口がこの型を要求する。

live-scan reportは exact 12 fields。

```text
schema_version = "freeze-live-scan-report/v1"
validation_head
lane
generation_number
bundle_digest_sha256
lifecycle_stage
enumeration
exemptions
holdouts
positive_control
results
aggregate
```

`enumeration` はexact 2 keys
`{before_sha256,after_sha256}` で、両値は64hex。上記top-levelは列挙どおりexact **12 fields**。

- exemptionsはactive chainから再導出したexact path/hash。
- enumeration before/afterはpath array canonical SHA-256。同値必須。
- holdoutsはrr80/rr20順、各 exact
  `{candidate_id,expected_hit_paths,actual_hit_paths,status}`。
- positive controlは固定fixture path/hashを含み、direct fixture hitを必須とする。
- resultsはS2-4 launch registry順。
- aggregateはactual resultsから導出。

lifecycle別 expected hits:

| lane/stage | expected |
|---|---|
| g0 legacy | rr80=[], rr20=[] |
| permanent `pre-measurement` | rr80=[], rr20=[] |
| permanent `ratified-floor` | verified measurement closure/bound artifactから再導出したpath集合と完全一致 |

未申告hitだけでなく、期待hitの消失も拒否する。positive-controlは全stageで必須。
scan後にbound artifactをno-followで再読し、bytes/mode不変を要求する。

static verifyが現在のlive hitだけを理由に失敗しないことは第1設計段§14の既存行に基づく。
launch gateを省略するconsumerは存在してはならない。

g0の`active_bundle`は§S2-3.5のraw root一致 + strict parse + 型変換だけをstatic guaranteeとする。
launch_validateはlive holdout scanとbound bytes不変を追加するが、legacy source/head/design-sourceの
現在有効性は主張・再検査しない。したがってg0 resolverのrefusal集合をfull verifier由来のdangling/driftへ
拡張せず、root不一致・parse不能・型違反に限定したままlaunch層へ渡す。

実物根拠: 現行 `s8b_ratified_freeze.LaunchValidatedFreeze` と`launch_validate()`、
`search_repository(exempt_exact=...)`。  
owner: **W-d**。

---

## §S2-11 U-A1裁定待ちhole

### S2-11.1 U-A1

決定権者: **ユーザー**。

選択肢:

1. 未発効activation window。A→Xまで有効、X後は期限で失効しない。推奨。
2. 発効後lease。X後も期限で失効。

裁定待ち項目:

- 選択肢ごとに別literalとする approval `schema_version` / `scope` のversion。activation-windowとleaseを
  同じschema/scope literalの意味違いとして実装してはならない
- approval expiry field名・型・必須性、および `approved_at` との順序
- approval/pointer/resolver/launch/use-timeのexpiry check-IDと、各IDのfield pointer/dependency/reason code
- `approval-record` CLIのexpiry argv、X時clock/committer epoch検査、再approval規則
- clock source、UTC secondsへの正規化、検査時刻のcapture位置、同一操作内でclockを一度だけ捕捉する契約
- activation-window案の「X時だけ検査し、X後はactive型を失効させない」規則
- lease案の `LaunchValidatedOfficialBundle` および全伝播objectに必要な `validated_at` / `expires_at`
  field、型、null規則、schema version
- lease案で19 consumerが**各use-time**に再検査する手順。launch時に作った型を期限後も保持・実走する
  ことを拒否し、resolver/launch結果の期限越えcacheと「一度passしたから再利用」を禁止する契約
- lease案のWAL/S-1 report/oracle observations/verdict/calibrationへのexpiry/clock観測伝播fieldと、
  欠落・不一致・期限切れreason code
- activation後のactive型失効規則、expiry/clock/cache/use-time/伝播の各mutation candidate

Git committer timeはbackdate可能である。static verifierが時刻真正性を保証するとは主張しない。
推奨案を選ぶ場合も、CLI/static gateは形式・順序検査に限り、真正性は人間承認運用に依存する。

**W-c開始条件**: U-A1裁定、本書へのfield/check/CLI/mutation差分反映、親による整合確認。
それ以前にW-cを開始しない。

### S2-11.2 その他の許可hole

| hole | 決定権者 |
|---|---|
| conformance vector期待出力literal | W-a開始時の親。外部参照実装で導出後レビュー |
| 19 consumerの先行predicate順 | W-d開始時の親 |
| record/member/WAL/report等の生成時確定件数・hash | 当該generation CLI。schemaの再導出規則に拘束 |

これ以外の「実装時に決める」を認めない。

---

## §S2-12 第1設計段正本への波及案

本節は第1設計段の変更本文案であり、本書だけで正本を書き換えた扱いにしない。
**本 wave (2026-07-22) で S2-12.1〜12.5 の全項を第 1 設計段へ適用済み** — 適用先の文言が最終形であり、
本節は起草時の案として凍結する (差分は同旨の表現調整のみ)。

### S2-12.1 §14 損失表への追記4行

```markdown
| G 後の current worktree source drift (現行 known verifier は current worktree 照合で拒否) | H_gen tree の宣言 closure が一致するため新 static verify は受理しうる | レビュー + 実行環境規律。launch/audit層に一般source driftを検査する層はない。R7(b)の直接帰結 |
| `frozen_at_head` のdangling (現行は拒否) | field廃止により当該identity検査はない | receiptのG/H_gen tree束縛 |
| `pre_oracle_head` は現行も任意の実在commitなら受理し、意図時点とのidentity一致を検査しない | 後継はcommit identityを持たず、G_pred/H_predの宣言semantic content同値で受理する | prediction semantic closure束縛。identityとcontentの交換であり一般source drift回収ではない |
| generation search直前だけuntracked regular hitを除去し、search直後に復元する操作 | tracked start snapshotは不変で、G/R/Q/Aがhitなしconfirmationを受理しうる | launch時live scanは最終実走を拒否するが、generation confirmation自体の偽承認は残余。隔離tree生成またはuntracked連続監視を本設計は主張しない |
```

### S2-12.2 §14 限界への追記1行

```markdown
- 実走時に実際に使用した orchestrator code、binary、`external/ccbench` gitlink identity は active bundle
  identity へ完全には機械束縛されない。static provenance は H_gen、live safety は launch/audit、
  残余はレビューと実行環境規律で回収する。
```

### S2-12.3 receipt 新規性の訂正案 (適用先 = 第 1 段 §7-R — 見出しの「§12」は起草時の誤記)

```markdown
現行 `s8b_ratified_freeze.py` が与える下限は generation introduction、approval、pointer、
revocation、cancellation の parser・履歴検査である。freeze-family transition receipt は現行機構の
拡張ではなく、第2設計段で定義する完全新設schemaである。
```

### S2-12.4 §3.1列挙snapshot文言訂正案

旧「holdoutの`search.file_enumeration`と同型」を次へ置換する。

```markdown
列挙依存は、H_gen tree のexact globから得たmember pathと各memberの再導出dispositionを全件保持する
member snapshotとして凍結する。snapshotはexact
`{enumeration_id, algorithm, pattern, members, file_count}` — enumeration ID、algorithm ID、
exact pattern、path昇順の`{path, disposition}`、`file_count`を持ち、説明文字列や件数だけでは集合の代用としない。
```

### S2-12.5 §13 pointer案

```markdown
第2設計段のexact仕様は `docs/freeze-permanent-design-s2.md` を正本とする。
未了は同書§S2-11のU-A1 (ユーザー裁定) と、§S2-2b.3のconformance期待出力literal確定
(W-a開始前gate、決定権者=W-a実装waveの親) の2件である。
```

---

## レビュー R1/R2 対応表

| 所見 | 反映先 |
|---|---|
| R1-1 | 第1段§7-Aの7 component訂正 + 本書冒頭、§S2-2 |
| R1-2 | R2-1方向を採用: §S2-3.5、§S2-10 |
| R1-3 | §S2-1.8、§S2-1.14、§S2-2b.4、§S2-5.4 |
| R1-4 | §S2-1.5、§S2-1.6、§S2-1.14 |
| R1-5 | §S2-8.3、§S2-9 `Me-keyset` |
| R1-6 | §S2-8.3、§S2-9 `Ma-registry-coupled` |
| R1-7 | §S2-4.3/4.5、§S2-9のreport/RV/CX/A分割候補 |
| R1-8 | §S2-1.12、§S2-7 |
| R1-9 | §S2-1.11、§S2-1.14、§S2-4.3/4.5 |
| R1-10 | §S2-3.1、§S2-3.4 |
| R1-11 | §S2-5.2、§S2-12.1 |
| R1-12 | §S2-11.1 |
| R1-13 | 冒頭状態行、§S2-2b.3、§S2-11.2 |
| R1-14 | 第1段§14訂正 + §S2-12.1/12.2 |
| R1-15 | 第1段§3.1訂正 + §S2-7、§S2-12.4 |
| R2-1 | §S2-3.5、§S2-10 |
| R2-2 | §S2-1.1 |
| R2-3 | §S2-1.8、§S2-1.14、§S2-2b.4、§S2-8.1 |
| R2-4 | §S2-2b.2 |
| R2-5 | §S2-1.12、§S2-7 |
| R2-6 | §S2-4.2〜4.5 |
| R2-7 | §S2-3.1〜3.4 |
| R2-8 | §S2-3.4「g1 source WAL専用の旧grammar」 |
| R2-9 | §S2-8.1/8.3、§S2-9 `Md-*-cutover` |
| R2-10 | §S2-8.3 |
| R2-11 | §S2-10 |
| R2-12 | 第1段§9/§12訂正 + 本書冒頭、§S2-8.1 |
| R2-13 | `docs/README.md`親訂正 + 本書冒頭の凍結design族宣言 |
| R2-14 | 冒頭状態行、本対応表 |

---

## 相談所見の反映対応表

| 所見 | 反映先 |
|---|---|
| X1 | §S2-1.3, §S2-1.7 |
| X2 | §S2-1.8, §S2-2 |
| X3 | §S2-4.2 |
| X4 | §S2-10 |
| X5 | §S2-3.5, §S2-4.4 |
| X6 | §S2-12.1, §S2-12.2 |
| X7 | §S2-12.1 |
| X8 | §S2-6 |
| X9 | §S2-6 導入後不変性 |
| X10 | §S2-1.3 projections |
| X11 | §S2-2b.1 |
| X12 | §S2-3.2 |
| X13 | §S2-4.1, §S2-9 |
| X14 | §S2-4.6, §S2-9 |
| X15 | §S2-2b.3 |
| X16 | §S2-4.6, §S2-8, §S2-9 |
| X17 | §S2-1.12, §S2-7 |
| X18 | §S2-1.6, §S2-1.12 |
| X19 | §S2-5.2 |
| X20 | §S2-11.1 |
| X21 | §S2-1.11, §S2-1.14 |
| X22 | §S2-4.1, §S2-4.5 |
| X23 | §S2-9 |
| X24 | §S2-5.4, §S2-8 |
| X25 | §S2-6 |
| Y1 | §S2-1.3 |
| Y2 | §S2-1.7, §S2-1.8 |
| Y3 | §S2-1.8, §S2-2 |
| Y4 | §S2-4.3 |
| Y5 | §S2-3.5 |
| Y6 | §S2-4.5 |
| Y7 | §S2-1.12, §S2-7 |
| Y8 | §S2-2b.1 |
| Y9 | §S2-5.2 |
| Y10 | §S2-2b.1 session区間 |
| Y11 | §S2-2b.2 import分離 |
| Y12 | §S2-8.1 |
| Y13 | §S2-4.6, §S2-8.1 |
| Y14 | §S2-8.3, §S2-9 |
| Y15 | §S2-8.3 |
| Y16 | §S2-5.4, §S2-8.1 |
| Y17 | §S2-3.5, §S2-6 |
| Y18 | §S2-3.5 |
| Y19 | §S2-11.1 |
| Y20 | §S2-9.1 |
| Y21 | §S2-4.1, §S2-9 |
| Y22 | §S2-9 `Me-g-extra-diff` |
| Y23 | §S2-2, §S2-9 `Mc-order` / `Mc-domain` |
| Y24 | §S2-8.3, §S2-9 |
| Y25 | §S2-8.2, §S2-11.2 |
| Y26 | 冒頭のdesign族/LIVING_DOCS宣言 |
| Y27 | §S2-1.4, §S2-12.3 |
| Y28 | §S2-1.11, §S2-1.14, §S2-4.3, §S2-5.4 |
