NO-GO

> sandbox が read-only のため `$D/s2-plan.md` 自体は作成していない。以下を同ファイルの本文とする。コード変更・テスト実行も行っていない。

## 1. NO-GO / GO 判定

現行 brief のまま scope 1〜8 を 1 session で完全実装することはできない。blocker は 6 件ある。いずれも恒真／恒偽 gate や producer 申告値の樿威化では閉じられず、凍結済み schema・記録要件を変更しないという制約内では解消不能である。dev-wave の stop rule に従い、実装 lane を起動してはならない。

| ID | blocker | 根拠と影響 | 解消に必要な入力 |
|---|---|---|---|
| B1 | `CMakeCache.txt` の raw pointer が schema にない | schema は `cmake_cache` を値 object とし、raw は `compile_commands` だけである (`receipt-schema-v1.json:94-171,805-825`)。一方、§6.3 は `CMakeCache.txt` 実体を含む 3 者再読を要求し (`record-items-v2.md:600-608`)、§8 は producer の `cmake_cache` 申告値を受理根拠にすることを禁じる (`:784-799`)。§7.1(12) と対応負例を実装不能。 | `cmake_cache_raw: fileRecord` を持つ schema 再発行、または CMakeCache path・bytes grammar を凍結する新裁定。現 schema の変更は本 session の制約 3 に違反する。 |
| B2 | durable intent の母集合と create-only provenance がない | `intent_ref` は各 attempt にあるが (`receipt-schema-v1.json:1092-1128`)、全 intent の canonical namespace/index、intent bytes grammar、発行履歴がない。したがって「全 attempt の exact 被覆」「qsub 失敗 row の欠落」「最初から `O_EXCL` で作られたこと」は最終 snapshot から判別不能 (`record-items-v2.md:470-476,581-582,777`)。同 path・異 digest の受領証内矛盾だけは検査できるが、§7.1(16) 全体にはならない。 | 承認済み intent inventory、canonical namespace、intent/marker writer capability と create-only 発行証拠。 |
| B3 | 別 stage の verification allocation receipt が validator 入力にない | §6.1 は pilot/main が同じ verification allocation を同じ bytes で持つことを要求する (`record-items-v2.md:583-585`)。schema に peer receipt pointer はなく、writer にも canonical peer receipt namespace がない。単一 receipt では比較不能。 | peer-stage receipt の固定 pointer、または receipt-set validator と canonical publication namespace の承認。 |
| B4 | `j_derivation` 等の transcript byte grammar と `J` の権威入力がない | `admission_telemetry[].receipt` は汎用 `fileRecord` だけで、kind ごとの JSON/key/数値表現が未定義 (`receipt-schema-v1.json:941-955`)。§4.12 は transcript 再計算を要求し (`record-items-v2.md:421-444`)、§6.8 は main slot 数を再導出した `J` と一致させる (`:677-684`)。追補 A は数式を定めるが transcript serialization と certified interval engine の契約を定めていない。 | kind ごとの transcript schema、canonical bytes、certified numerical algorithm/dependency、reference vectors の承認と pin。 |
| B5 | 観測終了から exec までの「他の作業なし」を観測する event stream がない | §6.5 は「他の作業・任意待機を挟まない」を要求する (`record-items-v2.md:623-630`)。receipt が持つのは observation と run の時刻であり、全作業を覆う順序付き event stream ではない。同一 receipt bytes を持つ「隠れ作業あり／なし」の 2 世界を validator は区別できない。 | trusted controller の全 event stream pointer、または「記録された event に限る」への明示的な裁定。後者を実装者が勝手に採るのは gate の緩和になる。 |
| B6 | §6.7(8) が要求する第 3 consumer が scope 外 | §6.7(8) は resolver・receipt validator・材料 report consumer の各々による独立な全履歴走査を要求する (`record-items-v2.md:654-667`)。brief は certified 側 consumer を明示的に scope 外とする (`s1-brief.md:15-17,43-44`)。resolver と validator の 2 回だけでは「§6 全件」を閉じたと言えない。 | 材料 report consumer を scope に追加する裁定、または本 session の完了主張を 2 consumer に限定する新裁定。`b03` consumer は追加しない。 |

B1〜B6 の解消前に、該当検査を skip、常時 reject、producer 申告との自己整合だけで代用する案はいずれも却下する。

## 2. file:line 粒度の実装プラン

以下は B1〜B6 の承認済み入力が揃った後に用いる条件付き実装計画である。

### A. approval manifest 実体 + loader

#### 固定 path と trust chain

- `orchestrator/preregistration/approval-manifest-v1.json:new:L1`
  - canonical UTF-8 JSON object、末尾 LF、duplicate key 不可。
  - 固定 path は P1 を維持する。
- `orchestrator/preregistration/_approval_manifest_pin.py:new:L1-8`
  - generator が出す `APPROVAL_MANIFEST_SHA256` だけを持つ private source pin。
- `orchestrator/preregistration/approval_manifest.py:new:L1-260`
  - `L1-28`: operational boundary と「source pin は resolver source を外部測定する機構ではなく、RP-2 が trusted Python/source とした境界内の literal」であることを docstring 化。
  - `L30-74`: immutable dataclass、exact-key 定数、構造化 error。
  - `L76-132`: duplicate-key 拒否、型・hex・repo-relative path・canonical JSON 検査。
  - `L134-205`: D282 payload との field-by-field exact 比較。
  - `L207-260`: vector index digest と index 内各 vector digest の検査。

固定 path だけでは manifest の差替えを防げないため、loader source 内の生成済み digestを最初に照合する。これは resolver source identity を測定・receipt 化する実装ではなく、RP-2 の「Python/resolver source は operational boundary 内」という裁定を利用する。

manifest の exact top-level key は次の 12 件とする。

| field | 導出元 |
|---|---|
| `schema_version = "t139-approval-manifest/v1"` | §7 の versioned manifest 要求 |
| `approval_fold_commit = "39d760985a5e37d20464c394760bf65596156566"` | D282 `F_r` literal |
| `decision_kind` | D282 payload |
| `forward_supersedes` | D282 payload の順序付き 2 行 |
| `preserved` | D282 payload の順序付き 3 行 |
| `target_core` | D282 の exact `(path, commit, sha256)` |
| `approved_blobs` | D282 の exact 6 role。target と合わせて 7 三つ組 |
| `erratum_application_order` | D282 exact 2 ID |
| `composed_sha256` | D282 exact digest |
| `not_approved_as_record_items_root` | D282 exact `{path,sha256,note}` |
| `operational_boundary` | D282 の改行を含む exact string |
| `conformance_vectors` | exact `{index_path,index_sha256}` |

`receipt_schema.sha256` は `approved_blobs.receipt_schema.sha256` に一意に置き、重複 field は作らない。`alpha_reservation` は exact-key 閉包に含めず、存在した時点で拒否する。

resolver の順序は必ず次とする。

1. `approval_payload.load_approval_payload()` で固定 `F_r` の D282 を読む。
2. checkout の実 HEAD を導出する。
3. source pin を使い、HEAD の固定 manifest path を `read_pinned_blob()` で読む。
4. manifest の duplicate/exact-key/digest を検査する。
5. D282 の全対応 field と exact 比較する。
6. vector index と各 vector digest を同じ HEAD から検査する。

不一致は `ApprovalManifestMismatch(reason_code, path, expected, actual)` とし、例として `path=("approved_blobs","receipt_schema","sha256")` を返す。role set 不一致は missing/extra role を別 field で返し、単なる「manifest mismatch」に潰さない。

正例は現行 D282 payload、生成 manifest、全 vector index が一致する 1 本を置く。

### B. resolver

- `orchestrator/preregistration/resolver.py:new:L1-480`
  - `L1-24`: operational boundary の実装解釈。「canonical checkout、その common Git directory、実行中の Python と絶対 path Git を信頼する。同一権限の source 改変は境界外」を docstring に置く。
  - `L26-112`: `PreregBinding`。`frozen=True`、通常 constructor 無効、private seal 経由だけで mint。
  - `L114-174`: 実 HEAD、exact commit、ancestor helper。
  - `L176-244`: approved identity、caller ref、addendum dependency triple。
  - `L246-316`: manifest/payload mismatch と erratum composition。
  - `L318-386`: alpha history、schema/vector closure、binding mint。
  - `L388-480`: public resolver。
- 外部署名は厳守する。

```python
resolve_effective_preregistration(
    repository_root, *,
    core_ref,
    addendum_a,
    addendum_b=None,
) -> PreregBinding
```

`measurement_head` 引数や `approval_manifest_ref` は追加しない。

`PreregBinding` の公開 field は少なくとも次を持つ。

- `core`, `addendum_a`, `addendum_b`
- `fold_commit`（D234 fold）
- ordered `errata`
- `approval_manifest`, `receipt_schema`
- `composed_core_sha256`
- `approval_fold_commit`
- `measurement_head`
- `alpha_reservation`（D282 payload から直接）
- private canonical repository root と private seal

`addendum_b` は現 manifest では未承認なので、`None` は pilot-ready、非 `None` は fail-closed とする。main-ready を偽装しない。

#### D234 決定 (7) の対応

| D234 | 実装箇所 | 検査 |
|---|---|---|
| (i) canonical core path | `resolver.py:new:L176-194::_require_canonical_core` | `core_ref.path == payload.target_core.path` の byte-exact 比較 |
| (ii) blob 実在・digest・承認 core | `resolver.py:new:L196-218::_resolve_approved_blob` → `blobref.py:102-160` | caller commit tree の regular blob、caller digest、D282 target digest の三重一致 |
| (iii) core commit が D234 fold の子孫 | `resolver.py:new:L150-174::_require_ancestor` | `88d68f... <= core_ref.commit`。`F_r` と混同しない |
| (iv) addendum と dependent core 三つ組 | `addendum_envelope.py:114-186` 後へ `_parse_dependent_core_ref`、`resolver.py:new:L220-244` | §0 YAML の exact 1 `core_ref`、exact 3 key、caller `core_ref` と完全一致 |
| (v) exact closed fields | `addendum_envelope.py:152-186::require_approved_addendum_a_fields` | erratum 適用後の `a01`〜`a13` exact set。approved addendum digest pin により値の差替えも拒否 |
| (vi) measurement ancestry | `resolver.py:new:L114-174` | `HEAD^{commit}` を resolver が導出し、core/addendum/errata/schema/manifest の commit が全て祖先 |
| (vii) core admission requirements | `resolver.py:new:L246-278::_parse_admission_requirements` | core metadata の `pilot_admission: requires_addendum_a` と `main_admission: requires_addendum_a_and_b` を exact parse。A 解決済みだけを pilot-ready とする |

追加で `F_r <= measurement_head` を要求し、approval manifest 発効前 checkout を拒否する。

`orchestrator/preregistration/alpha_history.py:new:L1-330` には §6.7(1)〜(7) の全履歴 walker を置く。resolver と semantic validator は同 helper を共有してよいが、各入口が fresh Git traversal を個別に起動する。cached verdict を共有しない。B6 解消後は材料 report も同様に fresh call する。

正例は現行 canonical repo の approved core/addendum A、`addendum_b=None`、現 HEAD から実 binding を得る統合例とする。

### C. Git trust root 部分集合

`orchestrator/preregistration/blobref.py` を次のとおり変更する。

- `:21-36`
  - `PATH` を allowlist から削除。
  - `_GIT_EXECUTABLE = "/usr/bin/git"`。
  - `_GIT_HARDEN` に `core.useReplaceRefs=false`、`core.commitGraph=false`、`core.fsmonitor=false`。
- `:163-177::_git_env`
  - ambient `GIT_*` を全て捨てる。
  - controlled values としてのみ `GIT_CONFIG_GLOBAL=/dev/null`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_LITERAL_PATHSPECS=1`、`GIT_NO_REPLACE_OBJECTS=1`、`GIT_OPTIONAL_LOCKS=0`、`GIT_TERMINAL_PROMPT=0` を再設定。
  - `HOME`、`XDG_CONFIG_HOME`、`LD_*`、`PATH` も継承しない。
- `:187-217::_git`
  - `["/usr/bin/git", "--no-pager", ...]` で起動。
- `:234-257::_require_safe_history`
  - shallow、replace、graft に加え以下を拒否。
  - effective local config の `extensions.partialClone`、`remote.*.promisor`、`remote.*.partialCloneFilter`、`core.alternateRefsCommand`。
  - `objects/info/alternates`、`objects/info/http-alternates` の存在。
  - `objects/pack/*.promisor`。
- `:102-160`
  - object-store safety 検査を全 object read より前に一度通す。
- `orchestrator/tests/test_t139_blobref_digest_binding.py:1-145` 後
  - 偽 `PATH/git`、ambient `GIT_DIR` 等、system/global config、local promisor、alternates、pager/fsmonitor/commitGraph の負例。
  - 通常の non-shallow local repo が通る正例。

`/usr/bin/git` の owner・group・SHA-256 は判定に使わない。したがって親実測 `0/0` と sandbox 上の見かけ `65534/65534` の差に依存しない。resolver source 自身の digest 記録も追加しない。

親は operational boundary の prose を worklog/記録段で書く。実装 child は `docs/dev-wave/**` を編集しない。

### D. raw snapshot API + consumer 結線

- `orchestrator/preregistration/raw_snapshot.py:new:L1-245`
  - `L1-45`: `RawSnapshot`、`SnapshotIdentity`、error。
  - `L47-79`: canonical repo-relative component validation。
  - `L81-164`: root と各 directory component を `os.open(..., dir_fd=..., O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)` で順に開く。
  - `L166-206`: leaf を `O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK` で開き、regular file を確認。
  - `L208-245`: bounded read、metadata・size・digest の照合。
- `orchestrator/campaign/contract_loader_binding.py:125-240` の component walk を先例として使うが、private function は import せず T-139 用に分離する。
- read 前後に leaf path stat と fd stat の次の tuple を全て一致させる。

```text
(st_dev, st_ino, st_size, st_mtime_ns)
```

各 directory component も親 `dir_fd` から read 後に再 stat し、名称差替えを拒否する。leaf は宣言 size + 1 byte まで読み、増加・短縮を検出する。

上限は `blobref.py:35` の既存 `MAX_BLOB_BYTES = 16 MiB` を共通定数として用いる。新しい恣意的 literal は作らない。16 MiB 超の raw は fail-closed となるため、B1〜B6 の再裁定時に実 producer の最大値も確認する。

- `orchestrator/preregistration/receipt_semantics.py:new:L86-132::_load_raw_closure`
  - 全 `fileRecord` を最初に列挙し、必ず `SnapshotSet.read_file_record()` 経由で読む。
  - 同 path が異なる size/digest で出現したら拒否。
  - semantic code 内の `Path.read_bytes()`、`open()`、直接 `os.read()` を AST 検査で禁止する。
- `orchestrator/tests/test_t139_raw_snapshot.py:new:L1-430`
  - regular file 正例。
  - root/intermediate/leaf symlink、FIFO/device、size/hash mismatch、read 中 inode/size/mtime 差替え、上限超過の負例。
  - semantic validator がこの API を実際に呼ぶ call-count/AST 検査。

### E. 受領証 writer の認可

- `orchestrator/preregistration/receipt_writer.py:new:L1-215`
  - 唯一の永続化入口:

```python
persist_receipt(destination, receipt_snapshot: bytes, *, binding: PreregBinding)
```

  - `binding` は必須 keyword-only、default なし。
  - `receipt_snapshot` は mapping/path ではなく exact `bytes` のみ受ける。
  - duplicate-key parse → Draft-07 schema → semantic validator → binding照合を同じ bytes から行う。
  - `preregistration` の core/addenda/fold/errata/manifest/schema/composed digest と、`measurement_checkout.repository_head` を binding に exact 照合。
  - 検査済みの同じ `bytes` object を `orchestrator/qualification/atomic_publish.py:24-123::publish_bytes` へ渡す。検査後の path 再読や再 serialize をしない。
- `orchestrator/tests/test_t139_receipt_writer.py:new:L1-520`
  - forged/直接構築 binding、別 HEAD、三つ組差替え、schema差替え、検査後 receipt mutation を全て publish 前に拒否。
  - 正例は temp Git worktree に vector raw を materializeし、実 resolver が mint した binding と正例 receipt を create-only publish。publish 後 bytes 一致も確認。
- `orchestrator/tests/test_t139_writer_boundary.py:new:L1-190`
  - `orchestrator/**/*.py` を AST 走査。
  - T-139 receipt schema literalを扱い、かつ `write_*`、write mode `open`、`os.open` write flags、`rename/link/replace`、`publish_bytes` を呼ぶ production function は `receipt_writer.persist_receipt` の reachable closure だけ許可。
  - package root から writer を export しない。
  - signature に required keyword-only `binding` があることを機械検査。
  - authorized positive が実際に 1 回 publish することを確認し、恒真 deny を防ぐ。

generic `atomic_publish.publish_bytes` を同一権限の非協調 code が直接呼ぶ攻撃は RP-2 operational boundary 外だが、repo 内の別 T-139 writer 経路は上記 AST inventory で固定する。

### F. 固定 semantic validator

- `orchestrator/preregistration/receipt_schema.py:new:L1-175`
  - `L1-62`: duplicate-key/non-finite/UTF-8/object parse。
  - `L64-118`: binding が pin した historical schema bytes を parse。
  - `L120-175`: `jsonschema.Draft7Validator` のみを使い、path順に安定した error を返す。
  - `Draft202012Validator`、`$defs`、`unevaluated*`、`format` に依存しない。
  - seam は `orchestrator/qualification/collector.py:287-305` と `artifacts.py:630-654`。既存 private validator は直接 import しない。
- `orchestrator/preregistration/receipt_literals.py:new:L1-310`
  - approved addendum A から導出した a01/a02/a03/a07/a08/a09 の exact table、phase cap、macro、schedule seed。
  - approved blob digest と anchor text の正例で literal drift を検出。
- `orchestrator/preregistration/receipt_semantics.py:new:L1-1180`
  - `L1-84`: immutable `SemanticFacts`、structured reason code。
  - `L86-132`: raw snapshot closure。
  - `L134-238`: preregistration/binding/pointer。
  - `L240-348`: indexes、IDs、references、ordinals、cardinality。
  - `L350-474`: planned schedule、a07/a09、wait。
  - `L476-628`: attempts、planned/actual、reason recomputation。
  - `L630-748`: build/source/TU/binary checks。
  - `L750-866`: run log、argv、`/proc/stat`。
  - `L868-1010`: allocation phase/time/monotonic。
  - `L1012-1085`: alpha history。
  - `L1087-1180`: orchestration。schema valid だけでは成功を返さない。

#### `reason_code` の再計算

`_derive_attempt_outcome()` は `attempt["reason_code"]` を一切読まず、raw facts から outcome を導出して最後に申告値と比較する。

- performance `completed`: allocation/marker/failure-null と 36-run 完全双射。
- verification `completed`: verification allocation、marker null、failure null、correctness 6、liveness 6、actual 0。
- pre-performance: marker null、actual 0、a03 failure 0、failure evidence 有。
- post-performance: marker、actual run、または route 3 のいずれか。
- correctness anomaly: terminal、correctness evidence、置換不可。
- replacement は pre-performance failure のみ、同じ slot。

route 3 は次の 6 条件を別 reason code で検査する。

1. observation が 1 件以上。
2. before/after raw が両方 snapshot 済み。
3. raw から short columns、negative delta、nonpositive total、window out-of-range、busy range 外のいずれかを再導出。
4. start/end が存在し単調、window 再計算可能。
5. non-null `malformed_reason` が評価順序と一致。
6. preflight route では marker null かつ actual run 0。

#### §8 の否定検査

`_derive_authoritative_facts()` と `_compare_producer_claims()` を分離する。recursive `TripwireMapping` を使い、前者が次の field を読んだ時点でテストを失敗させる。後者は claim mismatch により受理集合を狭める目的でのみ参照できる。

| producer field | authoritative source |
|---|---|
| `declared_use_class` | authoritative gate では参照しない |
| `reason_code` | raw/marker/run/evidence から `_derive_attempt_outcome` |
| `qsub_result.returncode` | eligibility には不使用。raw pointer の実在検査のみ |
| `exclusivity` | 診断 raw の実在だけ。単独性 verdict にしない |
| `fixed_inputs` | B4 解消後の transcript raw から再導出 |
| `composed_core_sha256` | binding の approved core+errata を再 compose |
| `schedule_sha256` | a09 seed から canonical table を再生成 |
| trace/analysis/`cmake_cache` | B1 解消後の configure argv、compile_commands、CMakeCache raw |

各 field について「raw が不適格なまま favorable claim に変えても不適格」「raw が適格でも claim 不一致は narrowing mismatch」の 2 組を置く。

### G. conformance vectors

- `orchestrator/preregistration/vectors/positive-v1.json:new`
  - exact positive receipt template、raw file bytes、binding/HEAD placeholder。
- `orchestrator/preregistration/vectors/negative-*.json:new`
  - exact key `{schema_version,id,base,mutations,expected_reason,covers}`。
  - JSON Pointer mutation と raw-byte mutationを分離。
- `orchestrator/preregistration/vectors/index-v1.json:new:L1`
  - sorted vector path、SHA-256、coverage ID。
  - index 自身は自己 digest を持たない。
- `orchestrator/tests/test_t139_conformance_vectors.py:new:L1-760`
  - positive materializer、negative runner、coverage exact-set、single expected rejection。
- `tools/build_t139_preregistration_pins.py:new:L1-180`
  - vectors を canonical parseし、sorted indexを生成。
  - index digest を manifest へ入れる。
  - manifest canonical bytes を hashし、`_approval_manifest_pin.py` を生成。
  - `--check` は無変更で再生成結果との差を検査。

順序は次で閉じる。

```text
vector JSON 群
  → generator が各 vector digest と index-v1.json を生成
  → index digest を manifest に生成
  → manifest digest を _approval_manifest_pin.py に生成
  → generator --check
```

これにより親の手入力も manifest/vector の circular digest もない。

### H. export 境界

- `orchestrator/preregistration/__init__.py:1-28`
  - docstring を「resolver/binding は実装済みだが、呼ぶだけでは投入されない。submit/receipt writer は package-root API ではない」へ更新。
  -既存 foundational export に `resolve_effective_preregistration` と `PreregBinding` だけを追加。
- `orchestrator/tests/test_t139_preregistration_binding.py:904-916`
  - forbidden set を `{"submit_pilot", "verify_receipt"}` に縮小。
  - resolver/binding が exact 2 名とも `__all__` にある正例を追加。
  - receipt writer、manifest loader、semantic internals は非 export のまま。

この部分解除は、全 gate・sealed binding・writer支配点が同一変更で完成した場合に限り D264 の理由を破らない。現状は NO-GO なので、先に export だけ変更してはならない。

### lane 分割と所有面

B1〜B6 解消後の分割は次とする。

| lane | 所有 file |
|---|---|
| A: manifest/resolver/Git | `blobref.py`, `addendum_envelope.py`, `approval_manifest.py`, `resolver.py`, `alpha_history.py`, `__init__.py`, resolver/manifest/Git/export tests |
| B: snapshot/semantic | `raw_snapshot.py`, `receipt_schema.py`, `receipt_literals.py`, `receipt_semantics.py`, snapshot/schema/semantic tests |
| C: writer/vectors | `receipt_writer.py`, `vectors/negative-*.json`, `vectors/positive-v1.json`, vector harness、writer tests、pin generator |
| Pin lane: serial | generator を実行し、`vectors/index-v1.json`, `approval-manifest-v1.json`, `_approval_manifest_pin.py` の生成物だけを所有 |

A は real manifest file を編集せず、Pin lane は loader source を編集しない。stage 5 統合前に各 lane の `git diff --name-only` を集合化し、交差が空であることを親が検査する。`docs/dev-wave/**`、凍結文書、registry、`b03` 関連 path は全 lane の禁止面とする。

各主要 gate の正例は以下のとおり。

| gate | 通る正例 |
|---|---|
| manifest | D282 と生成 manifest が全 field exact 一致 |
| Git | alternates/promisor のない通常の local repo |
| resolver | approved core/addendum A、現 HEAD、`addendum_b=None` |
| snapshot | 16 MiB 未満の regular file、read 前後 metadata 不変 |
| schema | duplicate-free Draft-07 positive receipt |
| semantic | `positive-v1` |
| writer | real resolver binding + `positive-v1` を create-only publish |
| vector pin | generator `--check` で全 digest 一致 |
| export | resolver/binding のみ部分解除、submit/verify 非 export |

## 3. §7.1 の 20 項目 → 実装箇所の対応表

| # | 実装箇所・検査 | 状態 |
|---:|---|---|
| 1 | `receipt_semantics.py:new:L240-282::_validate_kind_cardinality`。expected/observed、verification outcome 従属の correctness/liveness、stage 従属 telemetry 件数 | 実装可能 |
| 2 | `:284-318::_validate_ordinals` と `:350-374::_validate_predecessor_biconditional`。全 ordinal の 1-origin contiguous、`position==1 ⇔ START` | 実装可能 |
| 3 | `:320-348::_build_unique_indexes`。erratum ID、run/attempt/allocation ID、rehash pair、dependency pin 5 role | 実装可能 |
| 4 | `receipt_literals.py:new:L1-310` と `receipt_semantics.py:new:L376-420::_validate_approved_literals`。a07/a08/a09 exact | 実装可能 |
| 5 | `receipt_semantics.py:new:L422-474::_validate_planned_schedule`。`36×slots`、156 schedule row、1:1 table | 実装可能 |
| 6 | `:868-914::_validate_phase_contract`。role 別 phase 閉包、cap exact set | 実装可能 |
| 7 | `:916-948::_validate_binary_rehash`。到達点、arm 3 件、verification 0 | 実装可能 |
| 8 | `:476-628::_derive_attempt_outcome/_validate_reason_claim`。§5 全 branch、route 3 の 6 条件、replacement | 実装可能 |
| 9 | `:330-348::_validate_attempt_allocation_roles`。slot nullability と allocation role | 実装可能 |
| 10 | `:750-802::_derive_proc_stat_observation`。実列数、delta、total、window、malformed evaluation order | 実装可能 |
| 11 | `:630-686::_validate_translation_units_and_base_tree`。POSIX 再正規化、Git tree digest 再導出 | 実装可能 |
| 12 | `:688-748::_derive_compile_truth` 予定。configure argv / compile_commands / CMakeCache raw | **未実装: B1** |
| 13 | `:804-866::_validate_run_argv_and_log`。argv exact、`#FLAGS_`、ShowOpt map | 実装可能 |
| 14 | `raw_snapshot.py:new:L47-245` と `receipt_semantics.py:new:L86-132` | 実装可能 |
| 15 | `receipt_semantics.py:new:L950-1010::_validate_monotonic_order` | 実装可能 |
| 16 | `:604-628::_validate_receipt_local_create_only_consistency` で同 path/異 digest は拒否できるが、全 intent/create-only provenance は検査不能 | **未実装: B2** |
| 17 | `alpha_history.py:new:L1-330::validate_alpha_history` を validator が fresh call | 実装可能。ただし §6.7(8) 全体は B6 |
| 18 | `receipt_semantics.py:new:L868-1010::_validate_time_budget`。算術、phase elapsed、signal offset | 実装可能 |
| 19 | `:134-238::_validate_preregistration_binding`。receipt schema digest と binding/manifest pin | 実装可能 |
| 20 | `receipt_schema.py:new:L1-62::parse_receipt_strict`。schema検査前に duplicate key 拒否 | 実装可能 |

黙って落とす項目はない。(12) と (16) は現在の承認済み入力では実装不能として明示的に停止する。

## 4. conformance vectors の負例対応表

### §6 の各制約

| § | vector ID | 撃つ制約 | 状態 |
|---|---|---|---|
| 6.1 | `N-6.1-01-duplicate-id` | run/attempt/allocation ID 一意性 | 設計可 |
| 6.1 | `N-6.1-02-dangling-reference` | dangling reference | 設計可 |
| 6.1 | `N-6.1-03-omitted-intent` | intent 全数 exact 被覆 | **B2 により distinguishing vector 不可** |
| 6.1 | `N-6.1-04-omitted-qsub-failure-row` | qsub 失敗 row 欠落 | **B2** |
| 6.1 | `N-6.1-05-verification-count` | verification allocation exact 1 | 設計可 |
| 6.1 | `N-6.1-06-peer-verification-bytes` | stage 間同一 allocation bytes | **B3** |
| 6.1 | `N-6.1-07-cross-stage-slot` | stage-local reference | 設計可 |
| 6.2 | `N-6.2-01-completed-not-bijection` | completed performance の 36-run 双射 | 設計可 |
| 6.2 | `N-6.2-02-failure-not-strict-prefix` | failure run 列の strict prefix/evidence | 設計可 |
| 6.2 | `N-6.2-03-two-completed-attempts` | 1 slot に completed 高々 1 | 設計可 |
| 6.2 | `N-6.2-04-completed-verification-missing-performance` | verification完了時の slot別 performance allocation | 設計可 |
| 6.2 | `N-6.2-05-allocation-outside-consumed` | performance allocation slot closure | 設計可 |
| 6.3 | `N-6.3-01-performance-macro-one` | performance trace/analysis/cache = 0 | 設計可 |
| 6.3 | `N-6.3-02-correctness-macro-zero` | correctness の 2 値 = 1 | 設計可 |
| 6.3 | `N-6.3-03-three-truth-mismatch` | argv/compile_commands/CMakeCache の 3 者一致 | **B1** |
| 6.3 | `N-6.3-04-same-correctness-binary` | correctness binary と performance binary の分離 | 設計可 |
| 6.3 | `N-6.3-05-correctness-on-performance-allocation` | correctness scope が verification を指す | 設計可 |
| 6.4 | `N-6.4-01-wait-kind-seconds` | boundary 別 required wait | 設計可 |
| 6.4 | `N-6.4-02-adaptive-wait` | monotonic elapsed と required seconds | 設計可 |
| 6.4 | `N-6.4-03-argv-raw-mismatch` | raw argv と plan、digest | 設計可 |
| 6.4 | `N-6.4-04-run-log-map-mismatch` | `#FLAGS_` / ShowOpt exact map | 設計可 |
| 6.5 | `N-6.5-01-observation-count-or-prefix` | completed 36窓 / failure prefix | 設計可 |
| 6.5 | `N-6.5-02-window-or-exec-gap` | 10±0.1 秒、execまで5秒 | 設計可 |
| 6.5 | `N-6.5-03-hidden-work-between` | 他の作業・任意待機なし | **B5** |
| 6.5 | `N-6.5-04-busy-range-or-reobserve` | busy再計算、範囲、再観測禁止 | 設計可 |
| 6.6 | `N-6.6-01-noncanonical-schedule-bytes` | encoding/header/LF/row/order | 設計可 |
| 6.6 | `N-6.6-02-wrong-derived-permutation` | a09 key 再導出 | 設計可 |
| 6.6 | `N-6.6-03-replacement-new-slot` | replacement が同 slot を使う | 設計可 |
| 6.7 | `N-6.7-01-unsafe-git-history` | shallow/replace/graft | 設計可 |
| 6.7 | `N-6.7-02-wrong-history-range` | family root→HEAD full-history/reverse | 設計可 |
| 6.7 | `N-6.7-03-introduction-count-or-mode` | exact 1 introduction、100644 | 設計可 |
| 6.7 | `N-6.7-04-nonprefix-ledger-history` | edit/truncate/delete/rename | 設計可 |
| 6.7 | `N-6.7-05-noncanonical-jsonl` | duplicate key/canonical/LF | 設計可 |
| 6.7 | `N-6.7-06-duplicate-or-release` | family/ordinal一意、k=1、tombstoneなし | 設計可 |
| 6.7 | `N-6.7-07-entry-hash-or-first-commit` | entry digest、初出 commit | 設計可 |
| 6.7 | `N-6.7-08-independent-consumers` | resolver/validator/report の各 fresh traversal | **B6。data vector ではなく architecture conformance test が必要** |
| 6.8 | `N-6.8-01-wrong-pilot-slots` | pilot exact `[1..8]` | 設計可 |
| 6.8 | `N-6.8-02-main-slot-count-vs-J` | main `len(slots)==J` | **B4** |
| 6.8 | `N-6.8-03-object-slot-outside-consumed` | attempt/allocation/run slot closure | 設計可 |
| 6.8 | `N-6.8-04-reserve-counted-or-new-slot` | 予備非合算、replacement slot 再利用 | 設計可 |
| 6.9 | `N-6.9-01-phase-closure-or-nesting` | role別 phase、nested phase | 設計可 |
| 6.9 | `N-6.9-02-serial-sum-over-deadline` | 直列総和 ≤ deadline | 設計可 |
| 6.9 | `N-6.9-03-walltime-safety-mismatch` | deadline+safety=walltime | 設計可 |
| 6.9 | `N-6.9-04-phase-cap-or-signal-offset` | elapsed cap、TERM/KILL | 設計可 |
| 6.9 | `N-6.9-05-nonmonotonic-event` | allocation 内 monotonic order | 設計可 |
| 6.10 | `N-6.10-01-writer-without-binding` | writer authorization | 設計可 |
| 6.10 | `N-6.10-02-pointer-size-or-hash` | file/blob existence/size/hash | 設計可 |
| 6.10 | `N-6.10-03-symlink-or-read-race` | component nofollow/snapshot | 設計可 |

### §7.1 の 20 項目

| # | 対応負例 |
|---:|---|
| 1 | `N-7.1-01-kind-count`, `N-7.1-01-verification-dependent-count` |
| 2 | `N-7.1-02-ordinal-gap`, `N-7.1-02-start-biconditional-forward`, `...-reverse` |
| 3 | `N-6.1-01-duplicate-id`, `N-7.1-03-duplicate-erratum`, `...-rehash`, `...-dependency-role` |
| 4 | `N-7.1-04-a07-value`, `...-a08-source`, `...-a09-seed` |
| 5 | `N-7.1-05-run-count`, `N-6.6-02-wrong-derived-permutation` |
| 6 | `N-6.9-01-phase-closure-or-nesting`, `N-7.1-06-phase-cap-value` |
| 7 | `N-7.1-07-missing-rehash-point`, `...-verification-rehash` |
| 8 | completed performance/verification、pre/post/correctness/replacement の各負例に加え、route 3 の `N-5.2-01-no-observation`、`02-missing-raw`、`03-no-derived-failure`、`04-bad-time`、`05-malformed-reason`、`06-preflight-has-run-or-marker` |
| 9 | `N-7.1-09-attempt-allocation-role` |
| 10 | `N-7.1-10-short-columns`, `...-negative-delta`, `...-nonpositive-total`, `...-window`, `...-wrong-priority` |
| 11 | `N-7.1-11-noncanonical-tu-key`, `...-base-tree` |
| 12 | `N-6.3-03-three-truth-mismatch` — **B1 で作成不能** |
| 13 | `N-6.4-03-argv-raw-mismatch`, `N-6.4-04-run-log-map-mismatch` |
| 14 | `N-6.10-02-pointer-size-or-hash`, `N-6.10-03-symlink-or-read-race` |
| 15 | `N-6.9-05-nonmonotonic-event` |
| 16 | `N-7.1-16-same-path-different-digest` は作成可。全 intent/create-only provenance は **B2** |
| 17 | `N-6.7-01`〜`N-6.7-07` |
| 18 | `N-6.9-02`〜`N-6.9-04` |
| 19 | `N-7.1-19-receipt-schema-pin` |
| 20 | `N-7.1-20-duplicate-top-key`, `...-nested-key` |

B1〜B6 が未解消の現状態では、index coverage test は missing coverage を明示して失敗する設計とし、欠落 vector を「対象外」として除外して通してはならない。

## 5. 親の provisional 裁定 (P1)〜(P5) への賛否

| ID | 判定 |
|---|---|
| P1 | **採用** — 固定 JSON path/private helper は維持。ただし path 単独を trust root にせず、trusted source 内の生成済み manifest digest を先に照合する。 |
| P2 | **採用** — serial pin lane を維持するが、digest の直接編集ではなく deterministic generator が index→manifest→source pin を生成する。 |
| P3 | **採用** — 全 gate 完成と同じ commit で resolver/binding だけ部分解除。NO-GO 中に先行解除はしない。 |
| P4 | **採用** — blocker 解消後の 3 lane + serial pin lane。所有 file の交差は 0 に固定する。 |
| P5 | **採用** — `orchestrator/preregistration/vectors/` の versioned JSON 群。`FROZEN_MANIFEST` と `output/**` は変更しない。 |

## 6. 見積り

現行の約 1,900 production + 2,400 test は、全履歴 alpha、snapshot component walk、完全 semantic validator、否定データフロー検査、pin generator を過小評価している。

| lane | production | test | data |
|---|---:|---:|---:|
| A manifest/resolver/Git/alpha | 850〜1,050 | 750〜950 | manifest 1 file |
| B snapshot/schema/semantic | 1,350〜1,650 | 1,450〜1,750 | — |
| C writer/vector harness | 350〜450 | 550〜750 | vector JSON 1,800〜2,600 行 |
| Pin generator/output | 130〜190 | 150〜220 | index + generated pin |
| 合計 | **2,680〜3,340** | **2,900〜3,670** | **1,800〜2,600** |

B6 の材料 report consumer を本 session へ追加する裁定なら、さらに production 200〜300 行、test 250〜400 行を見込む。B1〜B5 の契約再発行・producer側取得実装はこの見積りに含めない。

## 総括

NO-GO — 現行の凍結入力と scope では 1 session 完遂不能。  
blocker は 6 件。  
最大 risk は、存在しない raw authority を producer の申告値で代用し false-green validator を作ること。  
read-only のためコード変更・テスト実行・`s2-plan.md` 書込みは行っていない。