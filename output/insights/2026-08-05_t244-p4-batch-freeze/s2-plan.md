# 静的実装プラン

これは指定ファイルだけを読んだ静的判断である。read-only のため編集・pytest・変異実走は行っておらず、テストが緑とは主張しない。

## 実測の再判定

親の W2 判定は正しい。W3 は結論こそ非適合だが、根拠の一部に訂正が要る。

- W2: [reflux_origin_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:445) の event 型に ordinal がなく、candidate commitment は `salt || raw candidate bytes` だけで作られる (`:552-557`, `:976-979`)。さらに commitment distinct (`:904-908`) と plaintext distinct (`:964-965`) が同一 wire の replicate を拒否する。親の非適合判定どおり。
- W3 の「任意 outcome が ledger を素通りする」は全面的には正しくない。書込み時は `_event_payload()` の `:629-635` が `"accepted" / "rejected"` 以外を拒否し、commit path は `:2408` で必ずそこを通る。replay も `:1845-1848` で再 canonicalize する。ただし reducer 単体の `:1001-1009` は確かに非閉包で、直接呼出しに対して fail-open。
- `result_sha256s` も暗号学的に完全未束縛ではない。prepared event の result commitments (`:576-603`) と長さ照合 (`:934-947`)、seal opening (`:984-1000`) がある。しかし意味は「任意 64hex result」に留まり、evidence digest として型付けされず、outcome を裏付ける evidence という契約がない。この意味で W3 非適合は正しい。

## W1〜W5 の現状

| 裁定 | 現状判定 | 根拠 |
|---|---|---|
| W1 | **部分適合**。ledger 面は適合 | 第一級 event 群は `reflux_origin_ledger.py:445-493`、canonical codec は `:560-804`、reducer は `:887-1065` に実在する。ただし D153 `:7595-7597` が含める producer/driver/formal consumer/proof-chain 結線はなく、静的検索でも production Python caller はゼロ。 |
| W2 | **非適合** | ordinal 不在、raw wire distinct 強制、上記のとおり。 |
| W3 | **非適合** | `EvidenceReference` は manifest のみ (`:184-188`, `:228-229`)。結果は opaque `result_sha256s` (`:469`, `:515`)。codec の outcome 閉包はあるが reducer 層は非閉包。 |
| W4 | **部分適合** | batch commit 時に cardinality 分の `queries_used` を消費し (`:915-918`)、`BatchTombstoned` は refund しない (`:1026-1034`)。一方 tombstone payload は batch ID だけ (`:664-667`)。prepared/sealed は全要素長を要求する (`:934-942`, `:955-963`) ため、実行済み prefix＋残 member tombstone を表せず、公開結果 transcript に cardinality 件の member row が残らない。 |
| W5 | **部分適合**。ledger/batch 面は適合 | origin-total counters は `_SemanticState` (`:807-821`) で累積し、policy は committed authority (`:1249-1324`) から reducer の `manifest.budget_policy` (`:899`) だけへ流れる。class は digest の exact set だけ検査 (`:1043-1060`) し referent を読まないため層分界も挙動上は正しい。ただし formal consumer 自体が存在せず、義務を実証できない。 |

## 推奨する v2 event 契約

この変更は v1 と非互換なので、manifest/authority schema は v1 のまま、runtime 側だけを明示的に v2 化する。

- `_EVENT_SCHEMA_ID` → `izanagi-reflux-origin-event/v2`
- `_HEAD_SCHEMA_ID` → `izanagi-reflux-origin-runtime-head/v2`
- `_DOMAIN_STATE` → `izanagi-reflux-origin-state/v2\0`
- runtime root `.../v1` (`:1168`) → `.../v2`
- authority JSON は空 registry のまま変更しない。

### member 型

`reflux_origin_ledger.py:36-58, 445-517` を次の構造へ置換する。

- `EvidenceDigest(sha256: str)`
- `CommittedBatchMember(query_ordinal, replicate_ordinal, candidate_commitment)`
- `PreparedBatchMember(query_ordinal, replicate_ordinal, candidate_commitment, result_evidence_commitment, constraint_commitment)`
- `OpenedBatchMember(query_ordinal, replicate_ordinal, candidate_salt, candidate_bytes, result_evidence_salt, outcome, evidence_digest, constraint_salt, constraint_sha256)`
- `TombstonedBatchMember(query_ordinal, replicate_ordinal, candidate_salt, candidate_bytes)`
- `SealedBatchMember(query_ordinal, replicate_ordinal, candidate_commitment, candidate_bytes, outcome, evidence_digest, constraint_sha256)`

各 batch event は parallel tuple 群ではなく `members: tuple[...]` を一つだけ持つ。これで index 対応を構造的に固定し、長さの異なる配列を `zip` する余地をなくす。

### member identity の正準 preimage

ordinal は **commitment preimage と event payload の両方**へ置く。

```text
MEMBER_DOMAIN =
  b"izanagi-reflux-origin-batch-member/v1\0"

MEMBER_JSON =
  canonical_json({
    "candidate_wire_b64": standard_base64(candidate_wire_bytes),
    "query_ordinal": query_ordinal,
    "replicate_ordinal": replicate_ordinal
  })

MEMBER_PREIMAGE = MEMBER_DOMAIN || MEMBER_JSON
candidate_commitment =
  SHA256(bytes.fromhex(candidate_salt) || MEMBER_PREIMAGE)
```

末尾 LF は付けない。例えば wire `b"10000"`、両 ordinal が 0 なら正準 bytes は次のとおり。

```text
b'izanagi-reflux-origin-batch-member/v1\x00{"candidate_wire_b64":"MTAwMDA=","query_ordinal":0,"replicate_ordinal":0}'
```

ordinal の意味は次で固定する。

- `query_ordinal`: origin-total の 0-based query slot。BatchCommitted で必ず
  `range(state.queries_used, state.queries_used + cardinality)` と完全一致させる。
- `replicate_ordinal`: 同一 batch 内で、同じ canonical wire がそれ以前に出た回数。例 `A,A,B,A` は `0,1,0,2`。
- commit 時は wire が秘匿されているため、replicate の canonicality は terminal opening 時に検査する。
- query ordinal の連続性だけで member identity は既に distinct になるため、さらに
  `len(set(member_identity)) == cardinality` を置くのは恒真検査になる。代わりに duplicate
  `candidate_commitment` は独立に拒否する。

### event payload

`reflux_origin_ledger.py:560-804` を nested member schema に改訂する。

- `batch-committed`: `cardinality`, `members`, `member_sequence_commitment`
- `member_sequence_commitment = SHA256(canonical_json(members))`
- `batch-results-prepared`: 同じ `(query_ordinal, replicate_ordinal, candidate_commitment)` と、result/evidence・constraint commitments
- `batch-sealed`: member ごとの candidate opening、result/evidence opening、constraint opening
- `batch-tombstoned`: batch ID だけでなく、cardinality 件すべての candidate opening を持つ tombstone member 列

全 object は `_exact_object()` で extra/missing key を拒否する。

## W3 の evidence 束縛

### outcome と evidence を一つの commitment にする

別々の outcome/result 配列を残すより、outcome と evidence digest を一つの preimage にまとめる方を推奨する。

```text
RESULT_DOMAIN =
  b"izanagi-reflux-origin-result-evidence/v1\0"

RESULT_PREIMAGE =
  RESULT_DOMAIN ||
  canonical_json({
    "evidence_sha256": evidence_digest.sha256 | null,
    "outcome": outcome
  })

result_evidence_commitment =
  SHA256(result_evidence_salt || RESULT_PREIMAGE)
```

閉じた outcome 語彙は次の三値だけとする。

- `accepted`: `EvidenceDigest` 必須、constraint は `None`
- `rejected`: `EvidenceDigest` 必須、constraint digest も必須
- `tombstoned`: evidence と constraint はともに `None`

`EvidenceDigest` は lowercase 64hex の型であり、manifest 用の path 付き `EvidenceReference` は再利用しない。per-query artifact の path authority がまだ存在しないためである。

### 検証点

`reflux_origin_ledger.py:530-663, 687-778, 950-1024` に次を置く。

1. event codec で型・閉じた outcome・exact member keys を検査。
2. reducer 冒頭でも同じ outcome/evidence matrix を再検査し、直接 `_apply_event()` を呼んでも fail-closed。
3. prepared member identity 列が committed member identity 列と完全一致することを検査。
4. seal 時に candidate、result/evidence、constraint の各 salted commitment を再計算。
5. 全 salt の event 内 distinct と origin-wide 未使用を、state 更新前に検査。
6. candidate wire を `reflux_ir.parse_wire()` → `encode_wire()` で再正準化し完全一致させる。現行 `:871-884` は後退させない。
7. 一つでも不一致なら sealed batch、counter、seen salts を一切更新しない。

ledger が保証するのは「この outcome がこの evidence digest と事前 commitment で束縛された」までである。formal consumer は別途、

- digest の referent を取得する、
- artifact bytes の SHA-256 を再計算する、
- authority receipt の verifier policy に従って evidence が outcome を支持することを検査する、
- rejected class digest の全 referent の実在・完全性を検査する、

必要がある。この wave でその consumer を実装したことにはしない。

## W4 の member tombstone と query 会計

`reflux_origin_ledger.py:807-868, 900-1063` を次の counter invariant にする。

- `queries_used`: commit 時に予約・消費した全 query slot。tombstone でも返却しない。
- `sealed_queries`: evidence を伴う `accepted/rejected` member 数。floor はこれだけを使う。
- `tombstoned_queries`: 実行されなかった member 数。
- IDLE 時は常に `queries_used == sealed_queries + tombstoned_queries`。
- open batch 中は右辺へ `len(open_batch.members)` を加えたものと一致させる。

部分早期停止は、`BatchSealed.members` を

```text
(accepted | rejected)*, tombstoned*
```

という prefix＋suffix だけに限定する。途中に tombstone を挟んだ後で結果を再開する列は拒否する。

全 member が tombstone の場合は `BatchSealed` との二重表現を避け、拡張した `BatchTombstoned` だけを canonical encoding とする。これは、

- committed member 全件を candidate salt/wire で開く、
- ordinal・commitment・wire canonicality・salt freshness を検査する、
- cardinality 件の `SealedBatchMember(outcome="tombstoned")` を公開する、
- `tombstoned_queries += cardinality`、`sealed_queries += 0`、
- batch 単位の既存 `tombstone_count += 1`、

という terminal batch event にする。

`OriginSnapshot` と `OriginSealed` に `sealed_queries`、`tombstoned_queries` を追加し、origin seal 時に supplied counters と ledger counters の exact 一致を要求する。

ここで「transcript 長」は **公開 member row 数が committed cardinality と同じ**という意味に固定する。JSON byte 長や event record 数まで一定にする意味なら、固定長 salt・固定幅 outcome・padding が別途必要であり、本案だけでは満たさない。段4で明示裁定すべき最大の曖昧点である。

## privacy と既存不変条件

`reflux_origin_ledger.py:2355-2398` の projection を更新する。

- `batch-sealed`: committed/prepared member commitments だけを head-prepared へ写す。
- `batch-tombstoned`: committed member commitments だけを写し、candidate salt/wire を head-prepared に出さない。
- outcome、evidence digest、constraint、全 salt は terminal event の append 前に head/runtime stateへ出さない。
- `read_sealed_batch()` の committed-head 検査 (`:2760-2774`) は維持する。

次は却下対象であり、実装候補に含めない。

- seal 前に outcome/evidence plaintext を head-prepared へ入れる。
- salt の origin-wide freshness (`:966-973`) を弱める。
- exact rejected class (`:1043-1060`) を subset 判定へ緩める。
- candidate wire canonicality (`:871-884`) を省略する。
- single in-flight phase gate (`:901-902`) を緩める。
- tombstone を query budget から返却する。

## codec feasibility

現行 `_MAX_BATCH_CARDINALITY` (`:83-87`) は「4 本の SHA 配列」前提なので v2 schema には使えない。

`reflux_origin_ledger.py:1581-1731` を次のように改訂する。

- legacy 上限 3912 を安全な探索 ceiling とし、real v2 codec で最大 cardinality を二分探索して `_MAX_BATCH_CARDINALITY` を確定する。
- 各 cardinality について、少なくとも以下を実際に `_record_frame()` へ通す。
  - BatchCommitted
  - BatchResultsPrepared
  - 最長の rejected BatchSealed
  - BatchTombstoned
  - sealed/tombstoned の head-prepared projection
- `_check_budget_codec_feasibility()` は `batch_min`、全 `floor.required_queries`、`qmax` のそれぞれについて全 frame を構築する。
- ledger total 上限計算 (`:1723-1731`) は normal seal path と whole-tombstone path の大きい方を使う。
- `_MAX_BATCH_CARDINALITY` を超える値は大きな tuple を作る前に拒否する。

event schema の増量により authority envelope は現状より狭くなる可能性が高い。実際の境界値は実装後に親が計算ノードで実測し、独立 literal として pin する。

## file:line 編集計画

### `orchestrator/campaign/reflux_origin_ledger.py`

| 現行行 | 変更 |
|---|---|
| `:2-16` | docstring を P4-compatible ledger prototype とし、physical query ordering・consumer referent 検証は未結線と明記。P4 充足とは書かない。 |
| `:36-87` | 新しい member/evidence 型の export、runtime v2 IDs、member/result domains、codec ceiling を定義。 |
| `:184-265` | `EvidenceDigest` と digest/preimage validation helper を追加。manifest の `EvidenceReference` は維持。 |
| `:445-517` | batch event と `SealedBatch` を nested member 型へ置換。snapshot/seal counter を追加。 |
| `:530-684` | member/result canonical preimage、nested event payload、閉じた outcome matrix を実装。 |
| `:687-804` | v2 payload parser。member object の exact keys、整数・base64・digest/null を検査。 |
| `:807-868` | `tombstoned_queries` と query partition invariant、commitment-only open batch semantic object。 |
| `:887-1065` | ordinal、replicate、opening、evidence、tombstone suffix、counter partition、exact origin counters を reducer で検査。 |
| `:1160-1169` | runtime root を v2 へ分離。authority path/schema は変更しない。 |
| `:1581-1731` | v2 の全 event/head projection に基づく構築的 feasibility。 |
| `:1805-1851` | v2 replay canonicalizationを維持し、codecだけでなく reducer defenseも必ず通す。 |
| `:2355-2398` | sealed/tombstoned prepared projection から plaintext と salt を除外。 |
| `:2737-2774` | snapshot に query partition を公開し、tombstoned batch も固定長 `SealedBatch.members` として読めるようにする。 |

### `orchestrator/tests/test_reflux_origin_ledger.py`

| 現行行 | 変更 |
|---|---|
| `:231-280` | `_batch_events()` を member object、origin-total query start、replicate、typed evidence、partial tombstone suffixに対応。 |
| `:315-413` | v2 独立 golden。詳細は次節。 |
| `:416-452` | transition matrix に full tombstone と partial tombstone seal を追加。 |
| `:522-868` | subprocess/crash 用 BatchCommitted constructor を新 member schema へ更新。 |
| `:719-848` | request identity、single in-flight、replicate positive、tombstone no-refund accounting を更新。 |
| `:1232-1339` | 独立 semantic preimage に member objects、sealed/tombstoned counters、v2 domains を反映。 |
| `:1343-1438` | v2 codec の literal 境界、tombstoneを除外した floor、origin counter exactnessを検査。 |
| `:1441-1583` | nested member の extra/missing key、bool ordinal、negative ordinal、invalid evidence/nullを追加。 |
| `:1586-1661` | outcome/evidence/constraint matrix、evidence tamper、partial tombstone固定長、exact classを検査。 |
| `:1663-1871` | v2 prepared projection の独立再構築、全 commitment category の salt freshness、plaintext非公開を検査。 |
| `:1873` 手前 | W2/W3/W4/W5 用の新規 focused vector を追加。 |

## golden とテスト vector

### 既存独立 golden

`test_v01_literal_manifest_event_state_and_receipt_goldens` (`:315-413`) は次の扱いにする。

- manifest literal (`:318-330`): manifest schema 非変更なので bit-identical のまま。
- event frame (`:333-352`): v2 schema と cardinality 件の tombstone member payloadへ書き換え、event SHA literal も更新。
- head frame (`:353-381`): head schema v2 により schema literal と record SHA が更新。
- state preimage (`:387-406`): state domain v2 と新 counter schemaへ更新。
- receipt shape (`:408-413`): unchanged を明示的に pin。
- 同 node に、member preimage と result/evidence preimage の手書き bytes、および固定 salt に対する SHA literal を追加する。

期待値は実装の `_event_payload()`、`_member_preimage()`、feasibility helper から生成してはならない。手書き JSON/base64 bytes と標準 `hashlib` だけで再構築する。

`test_v16_salt_contract_and_observer_reconstructs_preseal_bytes` (`:1686-1789`) も実質的な独立 golden なので、v2 member projection、head schema、state domain を literal で全面更新する。

### 新設 vector

- `test_v17_member_identity_literal_replicates_and_origin_query_accounting`
  - 同一 wire を `(q,r)=(0,0),(1,1)` として seal できる。
  - wire/q/r のどれか一つが変われば preimage と commitment が変わる。
  - query gap、重複 query、非canonical replicate、duplicate commitment を拒否。
  - distinct raw wire 数ではなく member 数だけ `queries_used` が増える。
  - invalid/noncanonical five-bit wire を seal/tombstone 両方で拒否。

- `test_v18_evidence_outcome_contract_and_fixed_member_tombstones`
  - accepted/rejected の evidence 欠落、tombstoned の evidence 混入を拒否。
  - rejected constraint 欠落、accepted/tombstoned constraint 混入を拒否。
  - evidence digest または outcome の片方だけを差し替えると opening mismatch。
  - partial tombstone は suffix のみ。
  - prepared/sealed/tombstoned/read model の member 数が committed cardinality と一致。
  - tombstone は floor に数えない。

- `test_v19_authority_policy_and_origin_total_query_partition`
  - event payload への policy/floor/qmax 注入を extra key として拒否。
  - manifest の qmax/floor だけが reducer を制御。
  - origin seal の supplied query counters と ledger total の不一致を拒否。
  - digest referent を ledger が dereference しないことは境界確認に留め、consumer 実在の証明とは呼ばない。

既存 V04〜V16 は constructor の機械更新だけで済ませず、V07/V08/V14/V16 の意味的 assertion を上記 invariant に合わせて改訂する。

## 受理集合への影響

production authority は [reflux_origin_authority_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_authority_v1.json:1) が空で caller もないため、現在の production 受理集合は全変更を通じて不変である。以下は結線後の潜在影響。

- v2 schema/runtime 分離: old v1 history を受理しないため **狭める**。
- 同一 wire replicate の許可: 正当な反復測定 origin を表現可能にするため **広げる**。
- contiguous origin query ordinal: gap・重複・過少計数 origin を拒否するため **狭める**。
- canonical replicate ordinal: 曖昧・偽装 replicate origin を拒否するため **狭める**。
- evidence-typed result bundle: evidence 未束縛 outcome を拒否するため **狭める**。
- `tombstoned` outcome: 正当な部分早期停止 origin を表現可能にするため **広げる**。
- tombstone suffix と固定 member 数: 選択的 hole・可変長 transcript を拒否するため **狭める**。
- tombstone を sealed floor から除外: 未実行 query で floor を満たす origin を拒否するため **狭める**。
- query partition counters の公開・exact seal: 正しい origin の意味は変えず、不整合 seal だけを拒否するため **狭める**。
- v2 codec feasibility: schema 増量で上限が低下すれば **狭める**、同値なら **変化なし**。
- authority-only policy と referent 分界の明文化: 現行 admission logic は既に同じなので **変化なし**。
- salt freshness、single in-flight、exact class、wire canonicalityの維持: **変化なし**。

## 段4で事前登録する変異候補

以下は未実走の登録案である。

| 変異 | 落ちるべき node |
|---|---|
| member preimage から wire を除く | `test_v17_member_identity_literal_replicates_and_origin_query_accounting` |
| member preimage から query ordinal を除く | 同上 |
| member preimage から replicate ordinal を除く | 同上 |
| origin-total query 連続一致を削除 | 同上 |
| replicate occurrence 検査を削除 | 同上 |
| duplicate candidate commitment 拒否を削除 | 同上 |
| raw candidate distinct を復活させる | 同上の同一-wire positive |
| seal/tombstone の wire canonicality を削除 | 同上の invalid wire negative |
| prepared member identity 一致を削除 | 改訂 `test_v16_commit_reveal_privacy_order_exact_class_and_positive_cycle` |
| cardinality 全件 opening を緩める | `test_v18_evidence_outcome_contract_and_fixed_member_tombstones` |
| reducer の outcome 閉包を削除 | 同上の direct `_apply_event` negative |
| accepted/rejected の evidence 必須を削除 | 同上 |
| tombstoned の evidence-null を削除 | 同上 |
| result/evidence commitment 比較を削除 | 同上の evidence tamper |
| rejected constraint 必須を削除 | 同上 |
| accepted/tombstoned constraint-null を削除 | 同上 |
| tombstone suffix 検査を削除 | 同上 |
| all-tombstone BatchSealed を許し二重表現を作る | 同上 |
| BatchTombstoned の member 数検査を削除 | 改訂 `test_v08_tombstone_no_refund_cardinality_accounting_and_no_provider` |
| tombstone 時に `queries_used` を返却 | 改訂 V08 |
| tombstone を `sealed_queries` に加算 | 改訂 `test_v14_independent_i_q_k_floor_boundaries_and_aborted_seal` |
| origin query partition exactnessを削除 | `test_v19_authority_policy_and_origin_total_query_partition` |
| tombstone head projection に candidate opening を混入 | 改訂 `test_v16_salt_contract_and_observer_reconstructs_preseal_bytes` |
| origin-wide salt freshnessを削除 | 同上 |
| second in-flight batch を許可 | 改訂 `test_v07_batch_prefix_cardinality_distinctness_and_single_inflight` |
| committed authority/live bytes 一致を削除 | `test_v12_git_anchor_symbolic_head_env_scrub_and_authority_version` |
| event payload から policy 注入を許可 | `test_v19_authority_policy_and_origin_total_query_partition` |
| exact rejected class を subset に緩める | 改訂 `test_v16_commit_reveal_privacy_order_exact_class_and_positive_cycle` |
| feasibility から sealed/head projection を外す | 改訂 `test_v14_independent_i_q_k_floor_boundaries_and_aborted_seal` |
| runtime schema bumpを戻す | `test_v01_literal_manifest_event_state_and_receipt_goldens` |

恒真・この面では kill 不可能な保証もある。

- 「実 query より先に BatchCommitted receipt を得た」は synthetic event tests だけでは証明できない。driver/caller が存在しないため、壊す production 行自体がない。
- 「producer が seal 前に別ログへ outcome を漏らさない」も ledger ファイルだけでは証明不能。
- evidence/class digest referent の実在・完全性は formal consumer 不在のため mutation target がない。
- 現行 V08 の `"provider" not in source` は consumer 義務の実装証拠ではなく、単に ledger が provider を持たないことの pin である。

これらを KILLED 扱いにすると恒真保証になるので、段4では明示的に residual と記録する。

## P4 充足判定

本 wave だけで **P4 充足とは名乗れない**。

この二ファイルで到達できるのは「D153 W1〜W5 の ledger-side 契約に適合する P4 batch-freeze prototype」までである。残るものは D159 決定4 (`docs/decisions.md:7890-7893`) の U-G 会計と同型である。

- producer が全 member commitment を先に commit し、receipt 後にだけ query を実行する結線
- driver が一 member を一実 query/evidence artifact に対応させる結線
- real authority manifest の登録と authority receipt の伝播
- seal 前の外部漏洩を防ぐ producer/storage 契約
- formal consumer が evidence/class referent を解決し、不在・不完全・policy 不一致を reject する受理集合変更
- proof chain/material report がその consumer 判定を必須にする結線

これらは並行 wave の所有面であり、本プランではファイル変更候補に入れない。必要なら別 wave の裁定パッケージとして、producer → receipt → query → prepared → seal → formal consumer の受理条件を引き渡す。

## 総括

- 中核は、parallel tuple を member object に置換し、`candidate wire + origin-total query ordinal + batch-local replicate ordinal` を正準 preimage と event payload の両方へ束縛すること。
- W3 は outcome と evidence digest を単一 salted result preimage にまとめ、三値 outcome と evidence/constraint matrix を codec・reducerの二層で閉じる。
- W4 は実行済み prefix＋tombstoned suffix、whole-batch tombstone の全 member opening、`queries_used = sealed_queries + tombstoned_queries` により固定 cardinality transcript と no-refund を保証する。
- 最大の risk は、「transcript 長」が member row 数を意味するのか、JSON byte/event record 数まで固定するのかという解釈差、および実 query/evidence referent がこの edit surface では観測不能なこと。
- 段4では、① outcome＋evidence を一 commitment にまとめる案、②全 tombstone は `BatchTombstoned` だけを canonical encoding とする案、③W4 の固定長を member cardinality と定義する案を明示裁定するべき。
- 本 wave の名乗りは prototype まで。P4 充足は producer/driver/authority/formal consumer/proof-chain 結線を含む U-G 型会計が終わるまで不可。