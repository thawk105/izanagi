# 8c 結線の前提設計 (origin ledger × 8c 自律 trial)

この文書は、8c 自律 trial へ reflux origin ledger を結線するために**先に決めておく必要がある 5 点**の
設計正本である。U-10 批准パッケージ (`output/insights/2026-08-06_t244-u10-budget-values/README.md` §7)
が「次に起票できるのは実装 wave ではなく設計 wave であり、そこで閉じるのは 5 点である」と定めた、
その設計 wave の成果物にあたる。

---

## 0. 射程・不変条件・名乗りの上限

**これは設計であって実装ではない。** 本文書が land しても、コード・テスト・本番 authority・
certified 選択・材料レポート・試行台帳のどの値も参照も変わらない。

固定する前提 (いずれもユーザー裁定または既決定):

- **D201** — 8c への origin ledger 結線は実装しない。本文書はその前提条件を書くだけである。
- **D183** — 本番 authority (`orchestrator/campaign/reflux_origin_authority_v2.json`) は
  71 bytes・`origins: []` のままとする。発行主体は人間である。
- **D114** — 承認上限は 1 generation。**D211** — repo 内 ever-issued cell 台帳は作らない。
- **D205** — 堅牢化の基準はアカデミアのプロトタイプ。
- **U-10 批准値** — `imax=4 / qmax=68 / kmax=1 / batch_member_row_count_min=2 /
  batch_distinct_candidate_count_min=1 / floor=(base 1, per_round 32, rounds 1, evidence_min 0)`、
  `F=33`、`R=1`。**実発行は「V-2 evidence 正本 + producer topology + 許可された実行経路」の
  3 条件成立後の人間承認 provisioning に限る。**

**名乗ってよいのは「8c 結線の前提 5 点の exact contract を設計した」までである。** 結線の完了、
発行 3 条件の充足、P3 / P4 の充足、production provisioning の解禁、物理実行の保証は名乗らない。
§9 が示すとおり、本設計を land しても **3 条件は 0/3 のまま**である。

---

## 1. 用語と field-path 規律

同名で別実体の識別子が複数あるため、本文書では**必ず完全修飾**する。裸の名前を使わない (D75)。

| 裸の名前 | 本文書での表記 | 実体 |
|---|---|---|
| `descriptor_sha256` | `authority.workload.descriptor_sha256` | authority manifest の workload digest |
| 同上 | `report.cells[i].descriptor_binding.output_sha256` | 実 report が残す descriptor digest |
| 同上 | `search_config["descriptor_sha256"]` | campaign config が持つ値 |
| `anomalies` | `wal.abort.payload.verify.anomalies` | terminal abort の構造化 witness |
| 同上 | `wal.verify_done.payload.anomalies` | 個数だけの計数 |
| `campaign_id` | `binding.campaign_id` / `PreparedCampaignIdentity.campaign_id` | registry 側 / 8c 側 |
| `state_commitment` | `EventReceipt.resulting_state_commitment` / `.current_state_commitment` | 履歴値 / 現在値 |

`cell_key` は `derive_cell_key()` が返す 4 要素 digest であり、**cell の一意名ではない** (§2.4)。

---

## 2. source closure — cell 同一性の閉包

### 2.1 現状

`derive_cell_key()` は次の 4 つの sha256 を順序付き canonical JSON として束ねる
(`orchestrator/campaign/reflux_origin_ledger.py:485`)。

1. `authority.workload.descriptor_sha256`
2. `axis_semantics_sha256`
3. `verifier_policy_sha256`
4. `environment_contract_sha256`

**ledger は 4 つの digest の中身を一切参照しない。** manifest の hash 形式と導出 identity を
検査するだけで、その digest が実在する bytes の digest かを確かめない
(`reflux_origin_ledger.py:1824-1892`、`:205-209`)。閉包はここで切れている。

### 2.2 referent 表 (どの producer のどの bytes か)

| referent | preimage となる bytes | 実成果物での照合点 | 現況 |
|---|---|---|---|
| `authority.workload.descriptor_sha256` | `s8b_descriptor._canonical_bytes(descriptor)` (sort key・compact separator・UTF-8・末尾 LF なし) | `report.cells[i].descriptor` を同規則で再直列化し `report.cells[i].descriptor_binding.output_sha256` と比較 | producer・runtime field ともに実在 |
| `axis_semantics_sha256` | 人間承認済み・名前付き axis-semantics artifact の raw Git blob bytes | WAL の `TriggerGateBinding.mask / predicate_sha256 / source` | **artifact が未存在** |
| `verifier_policy_sha256` | 人間承認済み・名前付き verifier-policy artifact の raw Git blob bytes (`legacy → s2` の ordered pass、accepted / rejected / tombstone 条件、witness 正規化を列挙) | 成功側は terminal `commit.payload.verify_configs`、失敗側は terminal `abort` | **artifact が未存在** |
| `environment_contract_sha256` | `ExecutionEnvironmentContract._canonical_obj()` の canonical JSON bytes | 物理実行 provenance の `contract_sha256` | producer・runtime field ともに実在 |

**live な Python source・runtime 定数・emitter の出力を hash して trust root にしてはならない。**
import closure と自己参照を閉じられず、producer と検査器が同じ誤りを共有すると全比較が緑になる。

### 2.3 `source-closure/v1` record

authority provisioning の入力となる create-once record。exact key 集合:

`schema_version` / `captured_commit_oid` / `authority_series_id` / `origin_id` / `cell_key` /
`referents`

`referents` は上表の 4 key ちょうどで、各値は
`preimage_ref = {path, sha256}` / `digest_rule` / `producer_field` / `runtime_field_paths` を持つ。
`preimage_ref.sha256` は **`captured_commit_oid:path` の raw Git blob bytes** の digest とし、
working tree の bytes を読まない。

発行時検査は次の順に固定する。

1. `captured_commit_oid` を full commit として 1 回解決し、その commit が**まだ新 authority entry を
   含まない**ことを確認する (authority 自身を source に含める自己参照の禁止)。
2. 4 つの `preimage_ref.path` を Git blob として読み、raw bytes の digest を record と manifest の
   双方と比較する。**authority loader の検査で代用してはならない** — loader は形式しか見ない。
3. workload projection を strict parse し、canonical 再直列化 bytes が blob と一致し、
   `report.cells[i].descriptor`・`report.cells[i].descriptor_binding.output_sha256`・
   authority の `records` / `threads` と一致することを要求する。
4. axis artifact は marker・5 reason の順序・5-bit LSB-first wire・mask `0..31`・`kUnset` を
   閉じた schema で持つ。実装との conformance は照合するが、**実装の bytes を trust root にしない**。
5. verifier artifact は ordered pass 集合と 4 条件 (accepted / candidate-attributable rejected /
   fail-closed / 単一 witness-class) を持つ。
6. environment projection を `resolve_by_contract_sha256` で一意解決し、物理実行時に
   provenance の `contract_sha256` と照合する。
7. 4 digest から `derive_cell_key()` を再計算し、closure record・authority entry・
   launch capability の `cell_key` が一致しなければ発行しない。
8. provisioning commit に、候補 authority bytes の sha256・`origin_id`・`cell_key`・
   closure record の sha256 を束縛した人間承認 receipt を置く。これは **1 origin の receipt** であり、
   全世代を列挙する ever-issued 台帳ではない (D211)。
9. 実行時には capability と result-evidence record が同じ closure digest を持ち、
   formal consumer が prospective identity と実成果物の双方を再照合する。

### 2.4 保証の範囲 — 「series 内」ではなく「同一 authority blob 内」

現 loader が拒否できるのは**同一 authority blob 内の同一 4-tuple 重複だけ**である
(`reflux_origin_ledger.py:1836-1865`)。series の世代連続性も ever-issued 性も実装に存在しない。

したがって、**同じ 4 referent のまま `authority_series_id` や budget を変えた新 blob を provision
すれば、同じ `cell_key` で別 `origin_id` を作れる。** これは設計で塞げない (塞ぐには D211 が
拒否した repo 内台帳が要る)。代わりに次を義務とする。

- **下流 consumer は `cell_key` 単独で集約してはならない。**
  必ず `(authority_blob_sha256, origin_id, cell_key)` の 3 つ組で scope する。
- 材料レポートが cell を集約表示する場合、この 3 つ組を出典として併記する。

これを守らないと、同じ cell の測定が独立試行として二重計上され、試行台帳の予算と
certified 選択の証拠数が水増しされる。

---

## 3. `result-evidence/v1` — V-2 の exact 化

### 3.1 なぜ必要か

ledger の `EvidenceDigest` は「claimed content digest」であり、**ledger は決して dereference しない**
(`reflux_origin_ledger.py:205-209`)。形式だけ正しい 33 個の digest を並べれば、
ledger 単体の構造検査は通る。物理実行と台帳を結ぶのは ledger ではなく、
**物理実行点で発行される create-only record と、それを読む formal consumer** である。

### 3.2 record schema

top-level exact key は 9 個。

`schema_version` / `issuer` / `origin_binding` / `trial_binding` / `ledger_member` / `p6_plan` /
`trigger_binding` / `physical_result` / `evidence`

| object | exact field |
|---|---|
| `issuer` | `kind` (固定 issuer ID)。**表示用であり権限の根拠ではない** (§3.6) |
| `origin_binding` | `authority_blob_sha256` / `source_closure_sha256` / `origin_id` / `cell_key` / `workload` / `axis_semantics_sha256` / `verifier_policy_sha256` / `environment_contract_sha256` |
| `trial_binding` | `launch_admission_record_sha256` / `campaign_id` / `workload` |
| `ledger_member` | `batch_id` / `iteration_index` / `query_ordinal` / `replicate_ordinal` |
| `p6_plan` | `purpose` (`source` または `p6-validation`) / `hypothesis_sha256` / `validation_plan_sha256` |
| `trigger_binding` | `mask` / `candidate_wire` / `trigger_gate_binding_commitment` |
| `physical_result` | `build_attempt_id` / `outcome` (`accepted` または `rejected` のみ) / `constraint_sha256` |
| `evidence` | `ordered_wal_ref` / `execution_provenance_ref` (いずれも exact `{path, sha256}`) |

record bytes は sort-key・compact separator の canonical UTF-8 JSON、末尾 LF なし。
`EvidenceDigest.sha256` はその raw bytes 全体の digest とする。
**record は自分の digest を自分の中に持たない** (自己 hash による恒真化の禁止)。

`ordered_wal_ref` は last-wins の `records_by_stage()` 射影ではなく、**当該 attempt の
順序付き record 列を凍結した create-only projection** を指す。last-wins 射影は legacy verify の
先行 record を落とすため使わない。

### 3.3 issuer・時点・置き場・create-only

issuer は、`run_campaign()` の terminal WAL と execution receipt を所有し、
`contract` / `binding` / `summary` / `layout` が同時に存在する **trusted physical harness の
最終化点**である。outer 8c ループ、planner / coder / auditor、report builder は issuer ではない。

書込み先は `report.cells[i].campaign_root` を根とする deterministic path:

```
<campaign_root>/reports/reflux-result-evidence/<origin_id>/<batch_id>/<query_ordinal>.json
```

順序は次に固定する。

1. ordered WAL projection と execution provenance projection を create-only で書き、
   file と親 directory を fsync する。
2. read-back して digest を確認する。
3. result-evidence record を create-only で書き、fsync・read-back する。
4. **その後にだけ**次の physical query へ進む。

強制手段は root confinement + symlink ancestor 検査 + `O_CREAT|O_EXCL|O_NOFOLLOW` + file fsync +
parent fsync + read-back 完全一致。`os.replace()` を使う atomic writer は**この record に使わない**
(final path を上書きできるため)。

### 3.4 outcome 対応

| 物理結果 | evidence record | ledger outcome |
|---|---|---|
| 同一 `build_attempt_id` の ordered WAL が terminal `commit` に到達し、`verify_configs` が verifier-policy artifact の exact ordered set と一致し、contract / receipt も一致 | `outcome=accepted`、`constraint_sha256=null` | `accepted` |
| terminal `abort` が candidate-attributable・非切詰め・既知 kind・構造整合済みの witness を持ち、正規化した class がちょうど 1 件 | `outcome=rejected`、`constraint_sha256=単一 witness-class digest` | `rejected` |
| witness class が 0 件または複数、切詰め、unknown kind、attempt 帰属が曖昧 | **record を発行しない** | 当該行以降を `tombstoned`、origin は aborted |
| build error / timeout / empty / parse error / role-invalid / infrastructure / competing tenant / duplicate skip / dry-pass / process crash | **record を発行しない** | 当該行以降を `tombstoned` |
| valid な validation 行が hypothesis を反証 | 当該行の record は発行する | 後続行を tombstone suffix、formal result は `P6NotDerived`、origin は aborted |

**複数 witness class から都合のよい 1 件を選ばない。** member は `constraint_sha256` を 1 個しか持たず、
`kmax=1` は単一 class policy として批准されている。複数 class を正式に数えるには member schema と
`Kmax` の意味を再裁定する必要があるので、ここでは fail-closed に aborted とする。

### 3.5 ledger member への 1 対 1 写像

| result record / run plan | `OpenedBatchMember` | `SealedBatchMember` |
|---|---|---|
| `ledger_member.query_ordinal` | `query_ordinal` | 同値 |
| `ledger_member.replicate_ordinal` | `replicate_ordinal` | 同値 |
| `trigger_binding.candidate_wire` の ASCII bytes | `candidate_bytes` | 同値 |
| `physical_result.outcome` | `outcome` | 同値 |
| raw record bytes の sha256 | `evidence_digest.sha256` | 同値 |
| `physical_result.constraint_sha256` | `constraint_sha256` | 同値 |
| run plan の各 salt | `candidate_salt` / `result_evidence_salt` / `constraint_salt` | seal 後は存在しない |
| **record 不在** | `outcome="tombstoned"`、evidence・constraint は `None` | 同値 |

`PreparedBatchMember` の 3 commitment は、上記 opening と run plan の salts から既存 preimage 規則で
計算する。member に存在しない field を存在するかのように写さない。

### 3.6 create-only は writer 認証ではない (保証の限界)

`O_EXCL` は**偽 record の上書きを防ぐだけで、最初の書き手を認証しない。** evidence root へ
書ける別 process (同一 UID を含む) が deterministic path へ先に整合的な 33 組を置けば、
honest な consumer は hash と terminal WAL を検査したうえで受理しうる。

**この穴は本設計では閉じない。** 閉じるには writer の権限分離 (別 UID / 別 namespace) が要り、
それは D205 のプロトタイプ基準を超える投資である。したがって:

- 本設計は **「evidence root へ書けるのは trusted harness だけ」という運用前提の上でのみ成立する**と
  明記する。
- 材料レポートは「ledger が受理した」を**物理実行の証明として書いてはならない** (§10)。
- 権限分離を作るか否かは §11 の裁定項目 (V-10) とする。

### 3.7 evidence bytes の解決 — content-addressed resolver

§4.1 の条件 1 は「raw digest が ledger の値と一致する」を要求するが、その bytes を
**どう取得するか**は本設計の他の節が決めていなかった。ここで閉じる。

**consumer は content-addressed resolver で解決する。** `evidence.ordered_wal_ref` /
`execution_provenance_ref` の `{path, sha256}` について、`path` から取得した bytes の
sha256 を再計算し、record の `sha256` と一致しないものを **resolver 段で拒否する**。
一致した bytes だけが §4.1 の条件 1・7 と §4.2 の双射判定の入力になる。

**発行者権威に裏打ちされた evidence receipt は作らない。** 受領証方式は「その受領証を
発行できるのは誰か」という trust root を新設する。権威は origin binding capability と
ledger の commitment 束縛が既に担っており、受領証は新しい事実を 1 つも足さない。

**ledger の分界は不変。** ledger は `EvidenceDigest` を dereference しない (§3.1)。
解決するのは formal consumer だけである。

**保証の上限。** content-addressed 解決が示すのは「取得した bytes は record が claim した
bytes である」だけであり、その bytes が物理実行に対応することは示さない。
それは §4.2 の双射条件が担う。resolver を物理実行の証明として名乗ってはならない。
また §3.6 の運用前提 (evidence root へ書けるのは trusted harness だけ) はここでも解けない —
偽の bytes と整合する digest を同じ書き手が置けば、再計算は一致する。

---

## 4. formal consumer と origin terminal

### 4.1 責務

formal consumer は ledger ではなく、P6 契約 (`derive_p6_cut`) を実装する trusted consumer である。
入力は issued capability・source closure record・create-only run plan・`read_sealed_batch()` の結果・
全 result-evidence record・ordered WAL。

`OriginSealed(aborted=False)` を許すのは次を**すべて**満たすときだけとする。

1. non-tombstone member ごとに exact 1 record があり、その raw digest が ledger の値と一致する。
2. tombstone member に record が無い。
3. origin / cell / authority blob / campaign / workload / descriptor / axis / verifier /
   environment / launch admission が capability と一致する。
4. `query_ordinal` / `replicate_ordinal` / wire / outcome / constraint が §3.5 の写像に一致する。
5. **物理 attempt との双射が成立する** (§4.2)。
6. base 1 行と mask `0..31` の validation 32 行が固定順で揃う。
7. accepted / rejected の WAL 条件が成立する。
8. P6 result が `P6Derived` で marginal set が空でない。
9. exact rejected class 集合・`Kmax`・floor が一致する。
10. **origin に全 tombstone batch が 1 つも無い** (§4.3)。

それ以外は `OriginSealed(aborted=True, constraint_class_sha256s=())` とする。

### 4.2 物理 attempt との双射 (record の使い回し防止)

「member ごとに exact 1 record」は member → record の全域性でしかない。record → 物理 attempt の
**単射**を課さないと、2 回の物理実行の WAL / provenance / `build_attempt_id` を 33 個の record から
使い回せる (`ledger_member` と claimed `trigger_binding` だけ変えれば digest は 33 通りになる)。

したがって consumer は次を必須とする。

- 33 record の `physical_result.build_attempt_id` が**相異なる**こと。
- `evidence.ordered_wal_ref` が指す WAL 区間が**互いに重ならない**こと。
- **WAL に記録された trigger binding の mask / wire / commitment が、record の
  `trigger_binding` と一致する**こと (claimed wire ≠ WAL wire を拒否する)。

### 4.3 formal-consumer receipt

「receipt が要る」だけでは実装者が存在検査で済ませ、恒真な gate になる。receipt は次を持つ。

- exact key 集合と canonical bytes 規則 (record と同じ規律)。
- **入力 state commitment** — consumer が読んだ ledger の `state_commitment`。
- **対象 `OriginSealed` の exact payload digest** — counters と class 集合まで含む。
- 検査した evidence 集合 (33 record の digest 列)・P6 出力・`enforcement_arm`・generator closure。
- issuer seal と one-shot 性 (同じ receipt を 2 回消費できない)。

capability client は、この receipt が **現在の state commitment と、これから送る `OriginSealed` の
exact payload** の双方に束縛されていなければ certifiable seal を送らない。
束縛が無い receipt は、別 origin・古い state・別 counter 用のものを再利用できてしまう。

### 4.4 ledger 単体では塞げない穴 — 末尾の全 tombstone batch

現行の seal 検査は candidate 下限を
`0 < batch.sealed_distinct_candidate_count < minimum` で見る (`reflux_origin_ledger.py:1618-1629`)。
**全 tombstone batch は `sealed_distinct_candidate_count == 0` なのでこの検査を素通りする。**
floor は non-tombstone だけを数えるので、33 行成功後に 2 行の全 tombstone batch を足しても
`sealed_queries=33` は変わらず、`aborted=False` を送れる (親が現物で確認)。

このとき試行台帳には tombstone を含む certifiable terminal が残る一方、材料レポートは
検査対象 33 行だけを参照でき、両者の batch / counter 集合が食い違う。

**本設計では consumer 側の条件 10 で禁止する。** ledger 自体を直す (certifiable seal で
全 tombstone batch を拒否する) のは受理集合の変更なので §11 の裁定項目 (V-6) とする。

---

## 5. 32 mask producer topology

### 5.1 batch は 1 つに強制される

P6 は全 validation mask・replicate・順序・予算を**最初の validation 結果より前に一括 commit**する
ことを要求する。一方 ledger の FSM は同時に 1 つの open batch しか持たない
(`IDLE → BATCH_RESERVED → BATCH_COMMITTED → RESULTS_PREPARED → IDLE`)。
先行 batch の結果開示前に後続 batch を予約できない以上、**validation 32 行は 1 batch に入るしかない。**

source 行だけを別 batch にすると、その batch は 1 行となり `batch_member_row_count_min=2` を
満たせない (padding tombstone で満たすのは恒真化なので採らない)。したがって:

**成功 topology = fresh origin・exact 1 batch・33 member。**

| member | `iteration_index` | `query_ordinal` | candidate wire | `replicate_ordinal` |
|---|---:|---:|---|---:|
| source base | 0 | 0 | `encode_wire(TriggerGateIR(m_s))` | 0 |
| validation mask `m` | 0 | `1 + m` | `encode_wire(TriggerGateIR(m))` | `m == m_s` なら 1、他は 0 |

member 数 33、相異 candidate 32、validation の replicate は各 mask について R=1。
source 行は validation の R に数えない。

### 5.2 実行順

1. source candidate・hypothesis・32 mask・順序・salts・`operation_id` 群・
   最大 reserve attempt 数を **create-only run plan** に固定する (§7.1)。
2. `BatchReserved(member_row_count=33, query_ordinal_start=0)`。
3. 33 個の candidate commitment を `BatchCommitted` する。
4. `query_ordinal=0` の source を物理実行する。
5. source が qualifying な single-class rejection のときだけ、mask `0 → 31` を順に実行する。
6. source が accepted / non-applicable、または query `q` で未証明の failure / crash が起きたら、
   **`q` 以降をすべて tombstone** とする (tombstone は終端 suffix でなければならない)。
7. 33 行すべてが non-tombstone かつ formal consumer が `P6Derived` のときだけ certifiable seal。
   1 行でも tombstone なら `sealed_queries < 33` となり floor を割るので aborted seal 以外を許さない。

reserve 後・commit 前に限り `BatchReservationAbandoned` による**再予約を 1 回だけ**許す
(`iteration_index=1` / `query_ordinal_start=33` / query `33..65`)。
**`BatchCommitted` 後は別 batch へ逃げない** — tombstone 行も replicate count を進めるため、
post-commit の全量再試行は `R` と `replicate_ordinal` の意味を分裂させる。

### 5.3 物理実行の単位 — duplicate skip を避ける

現 campaign ループは 1 run 内で同一 variant identity を `done` に入れて skip する
(`orchestrator/campaign/loop.py:242-246`)。source の mask `m_s` は validation sweep にも現れるため、
**source と `m == m_s` の validation 行を同じ campaign run で回すと 2 回目が物理実行されない。**
そこから既存 WAL を再利用して record を作れば、per-query の物理実行保証が破れる。

したがって本設計は次を要件とする。

> **1 query ordinal = 1 campaign run.** 33 行はそれぞれ独立した campaign run として実行し、
> `done` 集合を跨がせない。1 回の `drive()` の戻り値から 33 行を合成してはならない。

これは実行費用を 33 倍にする要件であり、批准時に想定されていない。§11 の裁定項目 (V-8) とする。
**現 8c の `drive()` は 1 candidate の outcome しか返さないため、この producer は現在存在しない。**

### 5.4 批准値との照合 (親の検算)

- `Qmax >= F`: `68 >= 33` 成立。
- `ceil(F/2248) = 1 <= min(Imax, Qmax // max(Bmin, candidate_min)) = min(4, 34) = 4` 成立。
- 成功時 `I/Q = 1/33`。pre-commit abandon を 1 回含めて `2/66`。
- 行数 33 ≥ 2、相異 candidate 32 ≥ 1、R=1、exact class 1 種なら `Kmax=1`。

**数値は通るが内訳が批准時と違う。** U-10 §5 択一 6 の余裕は「探索 2 行 + P6 32 行をそれぞれ 1 回
放棄できる」内訳だった。本 topology は 33 行を 1 batch に統合するので、
`4/68` が買えるのは **33 行 reserve の pre-commit abandon 1 回だけ**である。
**post-commit crash を 1 回生き延びる余裕はない** (§7.2 のとおり post-commit 再試行を禁じるため、
残り 35 query は certifiable recovery に使えない)。
U-10 §7 の定めどおり、この内訳変更と liveness 低下を明示して**再批准する** (§11 の V-9)。

---

## 6. launch admission が発行する origin binding capability

### 6.1 現状

`TrialBinding` は `manifest_sha256 / prereg_commit / measurement_head / trial_id / arm / holdout /
campaign_id / workload / ycsb_rratio` を持ち、descriptor・origin・cell・authority blob を持たない。
ledger の公開 API (`read_origin` / `commit_event` / `read_sealed_batch`) は capability を取らず、
caller が raw `origin_id` を渡せる (`reflux_origin_ledger.py:3454-3485`)。

### 6.2 `OriginBindingCapability/v1`

exact field:

`authority_blob_sha256` / `source_closure_sha256` / `origin_id` / `cell_key` /
`authority_workload` (`descriptor_sha256` / `records` / `threads`) / `axis_semantics_sha256` /
`verifier_policy_sha256` / `environment_contract_sha256` / `campaign_id` / `trial_workload` /
`measurement_head` / `store_scope` (`production` | `fixture`) / issuer seal

発行主体は launch admission gate とし、次を**一つの受理判断**として行う。

1. `assert_issued_trial_launch_admission` と `assert_rederived_launch_admission` を通す。
2. mode は `registered-effective` で `binding` は issued な `TrialBinding` であること。
   `explicit-unregistered-exploratory` に production capability を発行しない。
3. `PreparedCampaignIdentity.campaign_id` と `binding.campaign_id`、`binding.workload` と
   `trial_workload` を一致させる。
4. prepared descriptor の canonical digest・`records` / `threads`・
   `search_config["descriptor_sha256"]` を authority workload と一致させる。
5. provisioning receipt・source closure・authority manifest から
   `origin_id` / `cell_key` / `authority_blob_sha256` を**再導出**する。
6. expected な axis / verifier / environment を capability に束縛する。物理 site で actual な
   environment・WAL の verifier config・trigger binding を再確認するまで reserve を許さない。
7. `certifying` は **`False` のまま**とする (§6.4)。

### 6.3 ledger client の型分離

- production entry point は raw `origin_id` を公開面から外し、**issued capability を必須引数**にする。
  client は capability 内の `origin_id` だけを使い、呼出しごとに現在の authority blob・cell・
  store scope を再照合する。capability が無ければ read / reserve / commit / seal のどれも行わない。
- `store_scope=fixture` では**完全な fixture store client の明示を必須**とする。
  fixture capability だけ渡して client を省略した場合、`_production_store()` へ既定解決せず**拒否**する。
- production capability × fixture client、fixture capability × production client の組合せを双方拒否する。
- 現在の authority が空である間は production capability を発行できない。

### 6.4 `certifying=False` と ledger の `certifiable` は別物

ledger は non-aborted seal の terminal status を `"certifiable"` と書くが、
launch admission の `certifying` は `False` のままである。**この 2 語は同じことを意味しない。**

> ledger の `terminal_status == "certifiable"` は「この origin の台帳が形式条件を満たした」であり、
> **その trial が certified 選択へ昇格してよいという意味ではない。**

下流 consumer が ledger の terminal status だけを見て昇格させると、非認定 launch の結果が
certified 選択の受理集合へ入る。したがって **certified 選択へ入れる条件は launch admission の
`certifying` を正本とし、ledger terminal を昇格根拠にしない。** これを変えるには別途裁定が要る。

### 6.5 既定経路の bytes を壊さないための projection 規律

`launch_admission_record()` は exact 7 key
(`mode` / `certifying` / `reason_code` / `trial_id` / `workloads` / `binding` /
`activation_report_digest_sha256`) を返し、completeness 検査が同じ exact 集合を pin している
(`autonomous_trial_completeness.py:63-70`)。

したがって `origin_binding` を record へ足す実装は、次を守らなければ**既定 (originless) 経路の
run-start・report・`launch_admission_sha256`・lifecycle start row の bytes を変えてしまう**。

- **origin capability が発行された trial でだけ** `origin_binding` key を出す。
  未発行の trial では key 自体を出さない (`null` も置かない)。
- consumer (completeness・registry acceptance・report) の exact key 集合は、
  **同じ変更単位で** optional key として更新する。未知 key を一般に許す緩和はしない。
- 既定経路の bytes 不変は literal SHA golden で守らない (実 no-build drive は
  `loop_state.json` に wall clock を書くため golden が揺れる)。
  **非揮発 field 集合の比較**で守る。

`_finish_trial` へ引数を追加する場合は **originless な既定値付き**とし、
既定経路の呼び出し側を書き換えずに済む形にする。

---

## 7. 失敗・crash の event 対応と receipt 喪失照合

### 7.1 durable recovery envelope

最初の `BatchReserved` より前に、trusted controller が create-only の **run plan / recovery envelope** を
evidence root へ置く (ledger event ではない)。内容:

- issued capability と source closure の digest
- source hypothesis と validation plan の digest
- attempt 0 と reserve-abandon retry 1 の `batch_id`
- iteration / query の割付け、33 個の candidate wire と `replicate_ordinal`
- candidate / result / constraint の salts
- 各 event の安定した `operation_id`
- deterministic な evidence path 群
- 最初の `expected_state_commitment`

file と親 directory を fsync し、read-back する。role projection へ渡さない。
**ledger snapshot は `BATCH_COMMITTED` / `RESULTS_PREPARED` の open batch の salts や members を
公開しないため、envelope が無いと再送 payload を byte-for-byte 復元できない。**

### 7.2 failure → event 対応表

| 失敗・crash 点 | phase | 対応 |
|---|---|---|
| admission / source closure / actual env 照合 / run plan 作成の失敗 | `IDLE` (event なし) | ledger 無課金。candidate と hypothesis を差し替えず trial を失敗終了する |
| `BatchReserved` 呼出し後に receipt 喪失 | 不明 | **同一 `operation_id`・元の `expected_state_commitment`・同一 payload** を再送する。既 commit なら `replayed=True`、未 commit なら CAS 一致時だけ初回 commit になる |
| `BATCH_RESERVED` 中に producer 継続不能 | `BATCH_RESERVED` | `BatchReservationAbandoned`。I/Q は forfeited のまま返さない |
| `BatchCommitted` 呼出し後に receipt 喪失 | 不明 | exact `BatchCommitted` を再送する。新 `operation_id` や新 salts を作らない |
| 物理行が terminal WAL・provenance・record まで fsync 済み | `BATCH_COMMITTED` | record が連続 prefix にある限り次 ordinal へ進む |
| 物理行の開始後、record 作成前に crash | `BATCH_COMMITTED` | 当該 ordinal を最初の missing record とし、**その行から batch 末尾まで tombstone**。後続実行を再開しない |
| valid な行が hypothesis を反証 | `BATCH_COMMITTED` | 当該行を保存し、残りを tombstone suffix、`P6NotDerived` |
| `BatchResultsPrepared` の receipt 喪失 | 不明 | envelope の salts・record・tombstone suffix から exact commitment を再構成して同一 request を再送する (partial な result set は ledger が拒否する) |
| `BatchSealed` の receipt 喪失 | 不明 | exact opening 33 行を再送する。salt / result / constraint が違えば operation reuse mismatch で停止する |
| seal 後に formal consumer が crash | `IDLE` | `read_sealed_batch()` と create-only evidence から consumer を再実行する。ledger event はまだ足さない |
| formal result が `P6Derived` | `IDLE` | exact counters / class を持つ `OriginSealed(aborted=False)` |
| `NotDerived` / `NotApplicable` / `ContractError` / tombstone / evidence 不一致 | `IDLE` | `OriginSealed(aborted=True, constraint_class_sha256s=())` |
| `OriginSealed` の receipt 喪失 | 不明 | 同一 request を再送し `EventReceipt.replayed` で既 commit を識別する |

### 7.3 state commitment は global — 連鎖してはならない

`_state_commitment` は authority 内の**全 origin と runtime head** を含む
(`reflux_origin_ledger.py:2510-2542`)。`operation_id` も authority 全体で一意である。
したがって:

- **receipt を失った event `E` の再送**には、envelope に固定した **`E` 自身の元の
  `expected_state_commitment`** を使う。
- **次の event の base** には、直前の receipt の `resulting_state_commitment` を**使わない**。
  必ず **`current_state_commitment` (または再読した snapshot の値)** を使う。

これを守らないと、別 origin が間に commit しただけで CAS mismatch になり、origin が
`BATCH_RESERVED` / `BATCH_COMMITTED` に取り残されて I/Q だけを消費する。

ledger frame の末尾切れは replay が完全 prefix を検査した後に truncate する。
**consumer が「書けたはず」と推測して補ってはならない。**

### 7.4 新しい event 型は要らない — ただし材料が要る

- reserve 前後の取消 → `BatchReservationAbandoned`
- commit 後の未証明結果 → tombstone suffix + 既存 prepare / seal
- 科学的終端 → `OriginSealed(aborted=True/False)`
- receipt 喪失 → exact replay + CAS + `replayed`

**足りないのは crash event ではなく、元 request を byte-for-byte 復元する durable material である。**
新 event を足しても失われた salts や evidence は戻らない。

### 7.5 回復保証の外

- filesystem 全損、envelope の消失、同一 UID による悪意ある削除。
- **process crash で in-process seal (capability・lifecycle token) を失った場合。**
  Python の seal は同一 process 内の issued-value gate であって durable な capability ではない。
  別 process は ledger terminal も trial terminal も発行できず、origin は非終端のまま残る。
  この場合、**証拠を捏造して certifiable にしてはならない。** 非終端のまま記録する。

durable な capability の再発行契約は本設計に含まれない。含めるには launch admission gate の
永続化が要り、それは結線実装 wave の前にもう一段の設計を要する (§9 の残余)。

---

## 8. 予約より前の引き直しと事前登録

U-10 §7-2 のとおり、`BatchReserved` より前の candidate 生成失敗・provider 失敗は**課金されず
引き直せる**。P6 の validation sweep は 32 mask が決定的で生成段を持たないため P6 の主張には
効かないが、**source 行には効く**。

したがって本設計は次を要件とする。

- source candidate と hypothesis は、**最初の provider 呼び出しより前に**作られた create-only の
  run plan に固定し、その digest を capability と lifecycle へ束縛する。
- controller は run plan 作成後に source candidate を差し替えない。

これでも「run plan を書く前に何度でも試して、都合のよい candidate が出た時点で plan を書く」経路は
残る。**この残余は D205 の下で受容する** (U-10 §7-2 の判断を引き継ぐ)。
材料レポートは、source 行の事前登録が **run plan 時点**であって trial 開始時点ではないことを明記する。

---

## 9. 発行 3 条件との対応 — 現状は 0/3

| 発行条件 | 本設計が閉じる範囲 | 残余 (未成立の理由) |
|---|---|---|
| **V-2 evidence 正本** | exact schema・canonical bytes・issuer 位置・create-only 手順・outcome 対応・member 写像・formal consumer の 10 条件・双射・receipt 束縛を設計した | verifier-policy artifact、witness normalizer、構造化 integrity witness、physical writer、formal consumer、certifiable seal gate が**いずれも未存在**。create-only は writer 認証にならない (§3.6) |
| **producer topology** | fresh origin・1 batch 33 行・mask 順・ordinal 割付け・tombstone suffix・reserve-abandon retry を一意にした | 現 `drive()` は 33 物理 attempt を生産しない。1 query = 1 campaign run 要件が未確定 (V-8)。批准時の内訳と異なるため**再批准が要る** (V-9) |
| **許可された実行経路** | capability の exact field・発行判断・型分離・fixture 既定解決の拒否・projection 規律を設計した | **production runtime の初期化経路が存在しない** — `_initialize_locked()` は production を明示拒否し (`reflux_origin_ledger.py:2917-2919`)、初期化できるのは private fixture helper だけである。加えて `run_trial` → 実 client の公開 forwarding も未存在 |

**source closure は 3 条件すべての共通前提**であり、workload と environment の producer 規則は
存在するが、**axis-semantics と verifier-policy の名前付き正本、および provisioning receipt が
未存在**なのでこれも未成立である。

> **結論: 本設計は「3 条件を満たすための exact contract」を提示するが、3 条件のいずれも成立させない。
> 本番 authority の人間承認 provisioning は引き続き行わない。** authority は 71 bytes・
> `origins: []` を維持する。

---

## 10. 却下した案と恒真化の監査

| 却下した案 | 理由 |
|---|---|
| live Python source / runtime 定数 / emitter 出力を hash して trust root にする | import closure と自己参照を閉じない。producer と検査器が同じ誤りを共有すると全比較が緑になる |
| manifest の 64 hex を再計算せず信用する | 現 loader と同じ穴が残る |
| repo 内で series 横断・全世代の重複を調べる | D211 と矛盾する |
| axis / verifier artifact 不在時に固定 hash・空 object・「現実装と一致」を置く | 正本不在を緑へ変える恒真化 |
| outer `drive()` の `"certified"/"aborted"` から evidence を後付け合成する | attempt と構造化 witness を失う |
| `records_by_stage()` の last-wins 射影を evidence にする | legacy verify の先行 record を落とす |
| record 内の `issuer` 文字列を権限証明にする | 自己申告 |
| 複数 witness から 1 class を選ぶ | P6 契約違反。`Kmax=1` の意味を壊す |
| tombstone を evidence record として発行する | 「未証明を数えない」境界に反する |
| source 行の 2 行目を tombstone padding にする | 下限を実行せずに満たす恒真化 |
| validation を 2〜4 batch に割る | 先行 batch の結果開示前に後続を予約できない。P6 の一括 commit 条件にも反する |
| `Bmin` を 1 へ下げる | 正しさゲートの緩和 |
| post-commit crash 後に別の 33 行 batch を追加する | tombstone 行も replicate count を進め、批准済み `R=1` の意味が分裂する |
| capability を optional にし `None` なら production client へ落とす | fixture leak の再導入 |
| capability を持つだけで `certifying=True` にする | D114・P3 FAIL・P4 FAIL の名乗り上限に反する |
| receipt 喪失時に新しい `operation_id` を発行する | 二重 event と改変された継続を許す |
| `BatchCrashed` 等の新 event を足す | 既存 phase で表現できる意味を重複させるだけで、材料の欠落を解かない |

**書いてはならない主張:** 「ledger が受理した = 物理実行した」。ledger は evidence digest を
dereference しない。物理実行を主張できるのは formal consumer が §4.1 の 10 条件と §4.2 の双射を
検査した場合だけであり、それも §3.6 の運用前提の下でのみ成立する。

---

## 11. ユーザー裁定へ返す 5 件

| # | 択一 | 親の推奨 | 採らない場合の成果物影響 |
|---|---|---|---|
| **V-6** | 末尾の全 tombstone batch を ledger 側でも拒否するか。(a) certifiable seal で「全 tombstone batch を含まない」を要求する (受理集合の変更) (b) consumer 側の条件だけで運用する | **(a)**。consumer だけに頼ると、raw `commit_event` を持つ将来の caller が同じ穴を再現する | (b) のままだと、試行台帳は tombstone を含む certifiable terminal を持ち、材料レポートは 33 行だけを参照して batch / counter 集合が食い違う |
| **V-7** | production runtime の初期化経路をどう作るか。(a) authority provisioning と同じ人間承認手続で、entry 追加と runtime genesis を同時に書く一回限りの operation を**人間が**実行する (b) public な初期化 API を作る (c) 決めずに設計メモへ留める | **(a)**。(b) は `_initialize_locked` が production を拒否している防壁を公開面へ開く | 決めないと、発行 3 条件を満たしても最初の `read_origin` / reserve が「runtime 未初期化」で失敗し、試行台帳に origin 行が 1 件も作られない |
| **V-8** | 物理実行の単位を「1 query ordinal = 1 campaign run」とするか。(a) そうする (実行費用が 33 倍) (b) 1 run 内で 33 行を回す (source と同 mask の validation 行が duplicate skip され、`sealed_queries ≤ 32` で floor を割る) | **(a)**。(b) は fail-closed なら常に aborted、既存 WAL を再利用すれば物理実行保証が破れる | (b) を選ぶと producer topology は原理的に certifiable にならず、P6 の 32 mask 主張が成立しない。**裁定済み (D1616、(a))。** 実行形を持たない原因 2 つの解消案は「追記 (2026-09-05)」節 |
| **V-9** | `imax` / `qmax` の再批准。批准時の内訳 (探索 2 行 + P6 32 行をそれぞれ 1 回放棄) と本 topology (33 行 1 batch) は別物で、`4/68` が買う余裕は pre-commit abandon 1 回だけ。(a) 内訳だけ差し替えて `4/68` を維持 (b) post-commit crash を 1 回生き延びる余裕まで持たせて値を上げる (c) 現値のまま据置き再批准しない | **(a)**。(b) は §5.2 で禁じた post-commit 再試行を前提にするので、値を上げても certifiable recovery には使えない | (c) を選ぶと、批准値の根拠文書と実 topology が食い違ったまま authority が発行され、U-10 §7 の再計数義務に反する |
| **V-10** | evidence writer の権限分離を作るか。(a) 作らない — 「evidence root へ書けるのは trusted harness だけ」を運用前提とし、保証限界として明記する (b) 別 UID / 別 namespace の writer を作る | **(a)**。(b) は D205 のプロトタイプ基準を超える投資である | (a) の場合、材料レポートは「物理実行 0 件の偽 evidence を排除できるのは運用前提の下だけ」と明記する義務を負う。書かなければ proof chain が実際より強い主張になる |

---

## 12. 実装 wave へ引き継ぐ要件

前 wave (`output/insights/2026-08-06_t244-p3-8c-wiring/s4-adjudication.md` §7) の 8 要件のうち、
本設計が扱ったのは 2・3・6 の 3 件である。残り 5 件は**結線の実装 wave の受入条件**として残る。

1. `run_trial` から実 fixture client までの**公開経路の正例**を 1 本置く (private 直呼びにしない)。
4. `_finish_trial` の追加引数は originless な既定値付きにする (§6.5)。
5. 既定経路の bytes 不変は literal SHA golden ではなく非揮発 field 集合の比較で守る (§6.5)。
7. **変異事前登録を再構成する。** 少なくとも次を単一理由の変異点として登録する —
   §4.2 の双射 3 条件、§4.3 の receipt 束縛、§4.4 の全 tombstone batch 拒否、§5.3 の run 分離、
   §7.3 の `current_state_commitment` 使用、§6.5 の originless 既定 bytes。
   固定 0 の等価変異、proposal JSON の過剰決定、driver-local gate による見かけの kill は除く。
8. ledger 失敗の**公開経路での扱い**を決める (`run_trial` は例外を partial report へ変換するため、
   「伝播」だけでは公開 caller まで届かない)。

未着手のまま残る層も明記する。**completeness 検査**は現在の exact key gate が新 record を拒否する。
**材料レポート renderer** は現在 WAL と whiteboard しか読まず、ledger も result-evidence も読まない。
この 2 層に触れずに「結線した」と名乗ってはならない。

---

## 追記訂正 (2026-09-03) — §11 V-8 の「実行費用が 33 倍」は run の本数比であって費用比ではない

D1561 が求めた費用内訳の再測定を行った ([T-2261])。**既存 bytes は 1 バイトも書き換えていない。**
§11 の表の (a) 欄は「実行費用が 33 倍」のままである。本節はその追記訂正である。
測定の全文と一次資料は `output/insights/2026-09-03_t2261-v8-cost-breakdown/README.md`。

**§5.3 の「33 倍」は campaign run の本数比 (33 対 1) をそのまま実行費用の比と呼んだ数字である。**
費用は run の本数ではなく、run ごとの固定費 `F` と行ごとの費用 `R` の和で決まる。

現行コード (`c7ed56589`) の実測は次のとおり。

- run の前置費 (job 開始→最初の `build_start`) = **33 秒**。ただし job script の prologue と
  Python の import を含む未分離の区間で、`F` の点推定ではない。
- 1 行の費用 = **908.908 秒**と**374.728 秒** (同じ campaign の 2 変種)。行の費用は 1 つの値ではない。
- 行間費用 = 3 秒。これは (b) が払い (a) が払わない。
- 直列性検査の並列化により、同一変種・同一 commit 数の行が **1672.789 秒 → 908.908 秒**になった。

これらを `(a) = J + 33(F+R)`、`(b) = J + F + 32R + D + 31g` に入れると、
`J` と `F` の分け方の両端点で **倍率は 1.02〜1.11 倍**である。

**33 倍になるのは、比較相手が物理行を 1 本しか実行しないときだけである** (`33(F+R)/(F+R) = 33`)。
物理行を 32 本または 33 本実行する相手に対しては、`R` をいくら小さくしても 33 倍には届かない
(`R = 0` でも 8.6 倍)。そして「物理行 1 本から 33 record を作る」形は、§5.3 自身が
「per-query の物理実行保証が破れる」として退けた形である。

### §5.3 の行番号は古い

「現 campaign ループは 1 run 内で同一 variant identity を `done` に入れて skip する
(`orchestrator/campaign/loop.py:242-246`)」の行番号は現行位置と違う。現行は
`orchestrator/campaign/loop.py:522-529` である。**記述の意味はコードと一致している。**
duplicate skip が起きるのは `query_ordinal = 1 + m_s` の行であり、`m_s = 0` のときだけ 2 行目になる。

### V-8 (a) は現行コードで実行形が成立していない

費用より重い発見である。

- `campaign_identity` は `CampaignConfig` だけから決まり `genomes` を含まないので
  (`loop.py:194`、`ident.py:196-235`)、同じ cfg で 33 回呼ぶと identity は 33 回とも同じになる。
- `acquire_claim` は identity を key に `O_EXCL` で claim を作り、release API を持たない
  (`campaign_claim.py:74-79`、`383-434`)。**2 回目の `run_campaign()` は拒否される。**
- cfg を変えて 33 identity にすると、§6.2 の `OriginBindingCapability/v1` が `campaign_id` を
  1 つしか持たないことと、§4.1 条件 3 の campaign 一致要求に衝突する。

**claim を通すには 33 個の別 identity が要り、consumer を通すには 33 record が同じ `campaign_id` を
持つ必要がある。** V-8 の裁定はこの衝突の解消と一体で行う必要がある。

なお generic な reservation は 33 run の連続実行を妨げない (`reservation.py:26-55`、`223-275`)。
**scheduler へ 33 回投入する必要はない。** 止めているのは claim と capability の identity 設計である。

---

## 追記 (2026-09-05) — V-8 (a) の実行形: 論理 campaign と物理 campaign run の分離

D1616 が V-8 を (a) 「1 query ordinal = 1 campaign run」と裁定した。本節は、追記訂正 (2026-09-03) が示した
「(a) は現行コードで実行形が成立していない」原因 2 つ — campaign identity が候補の違いを含まず 33 run が
同じ identity になる、identity を分けると capability が `campaign_id` を 1 つしか持てない — の**解消案の
設計**である。**既存 bytes は書き換えず、§11 の V-8 行に裁定済みの印だけを足した。実装はしない。**
設計の逐語 (plan・敵対レンズ 2 本・裁定) は `output/insights/2026-09-05_t2293-8c-wiring-v8-identity/README.md`。

### A. 原因の再記述

- 8c の各物理 run は `Genome("silo", _BASE)` 1 個で `run_campaign()` を呼び (`p3_s4_loop_trigger_gating.py`
  `_run_one_iteration_resolved`)、33 行で変わるのは genome でなく `TriggerGateBinding` の mask / wire である。
  「identity が genome を含まない」は「identity が候補の違いを含まない」と読み替える。
- 同じ identity の 2 run 目を止めるのは claim だけではない。Pegasus (`allow_resume=False`) では
  `_assert_resume_allowed` (`p3_s4_loop_trigger_gating.py`) が同 layout の lock / loop_state / WAL / provenance を
  理由に、claim より先に拒否する。同 layout に WAL が残る限り `loop.run_campaign` の `done` seed が
  2 回目の同 variant を skip する。したがって解消は claim だけでなく **layout と WAL も物理 run ごとに分ける**。
- `campaign_claim.acquire_claim` は同一 `protocol_digest` (canonical preimage の full SHA-256) の LIVE owner と
  同一 path を拒否する。`spec_slug` は identity 文字列には入るが preimage には入らないため、
  「identity が違えば digest も違う」は一般則ではない。33 run は slug / search_tag が同じなので、
  short identity の相異から digest の相異が従う。
- `TopologyMember.planned_campaign_run_identity` (`reflux_origin_topology.py`) は既に存在し 33 member で相異を
  要求するが、production の producer も consumer も参照しない (test は固定文字列を入れる)。**束縛先の無い
  field** であり、本設計はこれを物理 run identity の正本にする。

### B. 2 層の identity (D75 の完全修飾)

| 層 | 表記 | 実体 | 個数 | 導出 |
|---|---|---|---|---|
| 論理 campaign | `binding.campaign_id` = `PreparedCampaignIdentity.campaign_id` = `OriginBindingCapability.campaign_id` = attempt slot の `campaign_id` = `trial_binding.campaign_id` = `execution_provenance.campaign_id` | registry / capability / slot / lifecycle / launch admission record が持つ**座標** | 1 trial に 1 つ | 現行どおり `ident.campaign_id(cfg)` |
| 物理 campaign run | `run_plan.members[q].planned_campaign_run_identity` = `execution_provenance.campaign_run_identity` = `report.cells[i].campaign_runs[q].campaign_run_identity` | claim / layout / WAL / `done` 集合の**単位** | query ordinal ごとに 1 つ (33) | `str(ident.campaign_id(cfg_q))` |

物理 cfg は次で作る。`CampaignConfig` に field を足さず、`trial` も変えない。

```text
cfg_q = replace(logical_cfg, search_config={
    **logical_cfg.search_config,
    "origin_campaign_run": {
        "attempt_capability_sha256": <AttemptSlotCapability.capability_digest_sha256>,
        "query_ordinal": q,            # exact int 0..32
    },
})
campaign_run_identity[q] = str(ident.campaign_id(cfg_q))
```

- 物理成分を `search_config` の名前付き key に置くのは、`trial` 文字列の接尾辞では generic な
  `CampaignConfig.trial` 名前空間と構文分離できないためである (別 caller の素の `trial="foo-q00"` と衝突しうる)。
  `canonical_preimage` は `search_config` を含むので identity・`protocol_digest`・claim path・layout root・WAL が
  すべて q 別になる。
- 物理成分に **attempt slot capability digest** を入れるのは D1190 の同型 (座標 + 測定世代 + ordinal) を
  保つためである。論理 cfg と q だけでは同じ trial の別 attempt (retry / 別 replicate / 別 prereg 世代) の
  33 run が同じ identity になり、過去 attempt の WAL を流用できる。同一 slot への再入は同 identity になり
  claim / resume gate で fail-closed、別 attempt は別 identity になる。resume を成功させるための決定性ではなく、
  **同一 slot の二重実行を fail-closed にするための決定性**である。
- 時刻・PID・乱数を含まない。33 identity と 33 preimage の相異は run plan 作成前に検査し、不一致・重複は
  予約前に停止する (`cfg_hash` は SHA-256 先頭 8 hex で、33 個の衝突確率は約 1.2e-7。衝突しても claim の
  `O_EXCL` と fresh check が拒否する)。
- `trial` を identity 以外に読む箇所 (`ident.is_a1_non_certifying_config`、`p3_b4_protocol.driver_kind_from_identity`、
  `p3_b4_closed_critic._driver_kind_from_cfg`) は 8c cfg では発火しない。`autonomous_trial_completeness.py` は
  `search_config` の exact key 集合と素の `trial` を再導出するので、origin cell 用の分岐が要る (§E)。

### C. 順序 — 予約より前に固定する

```text
capability 発行 (launch admission、論理 cfg)
  → attempt slot 予約 (t524 の slot、campaign_id は論理値)
  → 33 個の cfg_q / campaign_run_identity / preimage を導出し相異を検査
  → recovery envelope を create-only で書く (planned_campaign_run_identity = 導出値、caller に自己申告させない)
  → envelope digest を durable に束縛する (裁定 R1)
  → begin_attempt_observation
  → executor: q = 0..32
```

現行は envelope の write が `begin_attempt_observation()` より後にあり、observation 開始後・envelope 作成前の
crash で事前登録済み bytes が無い。上記の順序へ改める。§8 の「run plan の digest を capability と lifecycle へ
束縛する」のうち **capability への束縛は撤回する** — envelope が capability digest を含むため双方向にすると
循環する。参照は envelope → capability の一方向とし、envelope digest の durable な束縛先を R1 で決める。

registry 照合 (`trial_registry.assert_campaign_binding`) と capability 発行 (`issue_origin_binding_capability`) が
受けるのは**物理成分を足す前の exact `PreparedCampaignIdentity`** に限る。物理 cfg を渡せば拒否されるが、
それは呼出し順の帰結であって型の保証ではないので、実装 wave は受入要件と負例で固定する。

### D. 証拠側の結線 — 自己申告でなく現物から再導出する

- `execution-provenance` に `campaign_run_identity` を足す (schema 世代は R3)。`campaign_id` は論理値のまま残し、
  FC03 の 3 項等式 (`execution_provenance.campaign_id == trial_binding.campaign_id == capability.campaign_id`) を
  **残す**。
- ただし provenance の文字列同士の比較だけでは、§10 が却下した「record 内の `issuer` 文字列を権限証明にする」
  型の恒真化である (別 trial の 33 WAL を使い provenance だけ書き換えれば通る)。formal consumer は次を自ら行う。
  1. 各 record が指す物理 run の **`campaign.lock`** を content-addressed ref (§3.7) で解決して decode し、
     preimage から `campaign_run_identity` を再計算して `run_plan.members[q].planned_campaign_run_identity` と
     `execution_provenance.campaign_run_identity` に一致させる。
  2. 同じ preimage から `origin_campaign_run` を除いた論理 cfg を再構成し、`capability.campaign_id` と
     `attempt_capability_sha256` (slot capability digest) に一致させる。
  3. **envelope を evidence root の create-only file から再読**し、digest が R1 の束縛値と一致することを要求する。
     in-memory の envelope object を受け取って検査するだけでは、別 object / 別 path の envelope を渡して
     33 identity を宣言し直せる。
  4. `evidence.ordered_wal_ref` の解決先がその物理 run の layout 配下であることを要求する。
- §4.2 の双射 (`build_attempt_id` 相異 = FC05a、WAL 区間非重複 = FC05b) は「33 個の相異なる物理 attempt」を
  保証するが「どの layout で実行されたか」は保証しない。物理 identity 検査が追加で拒否するのは、
  **q10 と q11 の root / config を交換し provenance を整合的に再生成した入力**である。lock からの再導出が
  無ければこの入力を拒否できず、文字列比較だけの gate は変異を帰属できない冗長 gate (F28 型) になる。
- native WAL の trigger binding は `wal.log_trigger_binding` が `stage="trigger_binding"` / `payload` へ書くが、
  現 formal consumer の `_wal_trigger()` は fixture 形 (root `kind == "TriggerGateBinding"`) を要求する
  (D1555)。実装 wave は native decoder を足し、1 projection 内で shape family を 1 つに固定して mixed shape を
  拒否する。

### E. 実行器と report

- origin topology mode は `_run_workload` (`p3_autonomous_workload_trial.py`) が**論理 campaign の単一 layout を
  作るより前**で分岐し、`for generation in range(1, generations + 1)` に入らない。manifest の `generations == 2`
  は論理 trial の admission metadata として残し、物理 run の反復数には使わない。
- 各 q: `layout_q = exploration_campaign_layout(campaign_run_identity[q])`、`_assert_fresh_campaign_state(layout_q)`、
  既存 `_assert_resume_allowed`、`cfg_q` から再導出した identity が plan と一致、`CampaignSummary.campaign_id`
  (actual) が plan と一致 (plan からの複写を actual にしない)、前 q の evidence が fsync / read-back 済み。
- 現行 `drive_iteration` は `TopologyMember` を取らず、rejected / aborted の後も CERTIFIED_ACCEPTANCE の
  admission を呼ぶため P6 の qualifying rejection を戻り値で返せない。trigger module に origin 専用の sealed な
  物理 entry point を置き、public caller の任意 callback 差替えを許さない。
- 残時間: preflight の `ReservationCheck` を保持し、各 q の前に次 member の保守的上限で `ensure_remaining()` を
  検査する (`run_campaign` 自身は 1 秒しか要求しない)。不足なら以降を tombstone suffix にする。`max_wall_s` の
  既定 3600 s は 33 × 374〜908 s (T-2261 実測) に足りないので origin mode で別に決める。
- 失敗: **同一 process で捕捉した失敗**だけ tombstone suffix (§5.2 / §7.2)。process crash で seal を失えば
  §7.5 どおり非終端で、t524 の receipt v5 は成立しない。
- report: origin-bound cell は論理 `campaign_id` と `campaign_runs` (exact 33 件、各 exact 3 key
  `query_ordinal` / `campaign_run_identity` / `campaign_root`、q 昇順、相異、run plan と全件一致) を持ち、
  単数 `campaign_root` を出さない。originless cell は現行のまま。
- completeness (`autonomous_trial_completeness.py`) には `campaign_runs` を拒否する exact cell key gate は無く、
  拒否点は単一 `campaign_root`・素の `trial`・`generations == 2` の履歴・Layer 3 chain の 4 点である。
  `launch_admission.origin_binding` を発火条件に origin 分岐を置き、originless の受理集合は変えない。
  `layer3_report.py` の campaign 解決と `trial_registry.py` の acceptance issuer (`cells[0].campaign_root` 必須) も
  単一 campaign 前提なので origin-aware にする。origin cell の「complete」の権威は R2。

### F. 既定経路の不変と稼働中 wave

- すべての変更は origin capability 発行時だけ発火する。originless の run-start・report・`launch_admission_sha256`・
  lifecycle の bytes と受理集合は不変 (§6.5)。
- t524 (実験単位 = slot): attempt slot の `campaign_id` は論理値のまま。33 物理 run は 1 slot
  (`replicate_index == 0`) の内側で、slot / acceptance receipt v5 / `prereg_generation` に物理 identity を足さない。
  ただし `trial_registry.py` の report / measurement-target 部分は変わるので、実装 wave は t524 の着地後に着手する。
- t1851 (s8b の `campaign_run_id` / 測定世代): 変更 0。命名を `campaign_run_identity` に保ち s8b の世代・claim へ
  接続しない。

### G. 受理集合が動く写像 (述語は不変)

| 写像 | 旧 | 新 | 根拠 |
|---|---|---|---|
| cfg → claim path / layout | 同 trial の q ≥ 1 は q0 と同 identity で拒否 | q 別 identity で受理 | D1616 (a) の帰結そのもの。`acquire_claim` / `_assert_resume_allowed` の述語は不変 |
| WAL trigger binding の shape | fixture 形のみ | native `stage/payload` も受理 | D1555 が「provisioning と独立に必要」と明記した修理 |
| origin cell の report 形 | 単数 `campaign_root` | `campaign_runs[33]` | §6.5 の originless 不変規律の内側。originless は不変 |

### H. 却下した案

| 却下した案 | 理由 |
|---|---|
| claim に release / per-attempt key を足す | 拒否分岐の弱体化。release 不在は意図的設計 |
| identity に trigger wire を入れる | source 行と `m == m_s` の validation 行が同 wire で衝突する。ordinal だけが衝突しない |
| `generations` を 33 にする | manifest は `generations == 2` を exact 要求し、generation は LLM 探索の反復で物理 run の単位ではない。Pegasus の同 layout 再利用も解けない |
| identity を時刻・PID・乱数で分ける | D1190 が却下した乱数発行と同型。run plan 時点で再導出できない |
| `trial` 文字列の接尾辞で分ける (親 brief の当初案) | generic な `trial` 名前空間と構文分離できない。構造化 key と費用が同じ |
| 論理 cfg と q だけから物理 identity を作る (段 2 plan) | 同 trial の別 attempt の 33 run が同 identity になり流用できる |
| capability に 33 個の run identity を足す | capability は launch admission で発行され run plan より前。exact field・record・completeness の面が増え envelope と二重化する |
| 33 capability を発行する | capability は origin binding。33 capability = 33 origin になり §5.1 の 1 batch と矛盾 |
| FC03 の `execution_provenance.campaign_id` を物理値に置き換える | 3 項等式を崩し、別 trial の物理 run を流用する穴を開ける |
| provenance の文字列同士の比較で物理束縛とする | §10 の issuer 文字列型の恒真化。lock からの再導出が要る |
| completeness で lock を再読して防壁とする | formal terminal は completeness より先に ledger へ commit 済み。防壁は formal consumer に置く |
| 「33 layout が実在する」だけで物理実行を認める | 実行後に都合のよい 33 directory を plan へ対応付けられ、事前登録が恒真になる |

### I. 裁定パッケージ (ユーザーへ返す 4 件)

| # | 択一 | 親の推奨 | 採らない場合の成果物影響 |
|---|---|---|---|
| **R1** | run plan (envelope) digest の durable な束縛先。(a) lifecycle `start` 行に origin-only optional key `origin_run_plan_sha256` を足す (§6.5 の projection 規律) (b) ledger `BatchReserved` payload に載せる (ledger 受理集合の変更、V-6 と同型) (c) in-process seal だけ | **(a)** | 束縛が無いと別 object / 別 path の envelope で 33 identity を宣言し直せる。(c) は process crash で消える |
| **R2** | origin cell の「complete」の権威。(a) issued capability + formal-consumer receipt + 33 `campaign_runs` の lock / WAL 再検査からなる origin 専用 completion を、通常 cell の「全 campaign が admitted」と分けて置く (b) 33 物理 campaign すべてに通常 Layer 3 admission を要求する | **(a)**。(b) は P6 が qualifying rejection を必要とするため成立しない | 決めないと completeness と registry acceptance が単一 root 前提のまま origin cell を拒否し、結線実装 wave が受入条件を持てない |
| **R3** | `execution-provenance` の schema 世代。(a) `execution-provenance/v2` を新設し v1 は historical decoder (origin consumer は v2 のみ受理) (b) v1 を in-place で 8 key に拡張 | **(a)** | (b) は同じ schema 名が異なる exact key 集合を表し、fixture と将来 artifact の世代判別ができない |
| **R4** | (確認) §G の 3 写像を D1616 / D1555 / §6.5 の範囲内として実装 wave へ渡してよいか | **可** | 否なら V-8 (a) は実行形を持てず D1616 へ戻る |

V-6 / V-9 / V-10 は未裁定のまま。**発行 3 条件は 0/3、本番 authority は 0 件、結線実装 wave の起票制限
(2026-08-12) は本追記で変わらない。** 本節が閉じたのは「V-8 (a) の identity / capability 衝突の解消案」だけである。

### J. 実装 wave への受入要件 (§12 への追加) と変異事前登録の候補

| # | 受入要件 | 変異位置 / 無効化する述語 / 期待する赤 |
|---|---|---|
| 9 | 33 個の cfg_q / identity / preimage を決定的に導出し相異を検査する。入力は (論理 cfg, slot capability digest, q) | `p3_autonomous_workload_trial.py` の導出 helper。q を固定 0 へ。run plan 作成が重複 identity で赤 |
| 10 | registry 照合と capability 発行は物理成分を足す前の exact `PreparedCampaignIdentity` だけを受ける | 同 preflight。cfg_q を渡す負例が `assert_campaign_binding` で赤 |
| 11 | envelope は slot 予約後・observation 開始前に create-only で書き、planned identity は helper が計算し caller に自己申告させない | 同 envelope builder。順序を observation 後へ変異、または caller 値を通す変異で赤 |
| 12 | executor は generation loop と排他で、各 q に fresh check・identity 一致・actual (`CampaignSummary.campaign_id`) 一致・残時間検査を掛ける | `_execute_origin_topology` (仮名)。全 q で q0 layout を再利用する変異、actual を plan から複写する変異で赤 |
| 13 | provenance は `campaign_run_identity` を必須 key に持ち (R3 の世代)、consumer は FC03 の 3 項等式を維持する | `reflux_result_evidence.py` の exact key。必須を外す変異で欠落 provenance の受理が赤 |
| 14 | formal consumer は各 record の `campaign.lock` を decode し、物理 identity と論理 campaign を再導出して plan / capability と照合する | `reflux_formal_consumer.py` の新検査。q10 / q11 の root と config を交換し provenance を整合再生成した負例が赤 (FC05a〜c は通る) |
| 15 | formal consumer は envelope を disk から再読し R1 の束縛値と digest 一致を要求する | 同。別 path の envelope を渡す負例が赤 |
| 16 | FC05a の `build_attempt_id` 相異は独立に維持する | `_validate_bijection`。identity 33 個が正しく attempt ID を 1 件重複させた負例が赤 |
| 17 | native WAL の `stage/payload` shape を検証し、1 projection 内の shape family を 1 つに固定する | `_wal_trigger` / `_validate_wal_outcomes`。native decoder 無効化で `wal.log_trigger_binding` 相当の正例が FC05c / FC07 で赤、mixed shape の負例が赤 |
| 18 | origin report の `campaign_runs` を exact 33 件で再検査し、originless の bytes と受理集合を変えない | completeness の origin 分岐。q8 / q9 入替えの負例が赤。分岐を常時発火へ変異すると originless の projection 比較が赤 |

実装 wave が触れる予定の file: `p3_autonomous_workload_trial.py`、`p3_s4_loop_trigger_gating.py`、
`reflux_result_evidence.py`、`reflux_formal_consumer.py`、`autonomous_trial_completeness.py`、`layer3_report.py`、
`trial_registry.py` (report / measurement-target 部分、t524 着地後)、対応する test と fixture builder / baseline。
`reflux_origin_topology.py`、`campaign_claim.py`、`loop.py`、`ident.py`、`model.py`、`s8c_acceptance_receipt.py`、
`s8b_*` は変更しない。**「provenance 33 値の相異」単独の変異は登録しない** — planned 全件一致と envelope 側の
相異検査が同じ入力を先に拒否し、単一理由にならない。

ledger producer (reserve〜seal の状態機械)、qualifying rejection から witness class を導く normalizer、
material report renderer は §9 の「未存在」のままで、本節は設計しない。
