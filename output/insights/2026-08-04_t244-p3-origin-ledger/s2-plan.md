# 段 2 実装プラン — reflux origin ledger

## 0. 前提訂正と射程

親 brief の「4 性質が repo 全体で未被覆」という記述は erratum により撤回済みである。qualification 側には既に event index・hash chain・二相 outcome・exact-idempotent replay がある（`brief-erratum-1.md:3-31`、`orchestrator/qualification/attempt_ledger.py:169-309,344-473`）。したがって本 wave の純増は、これらを reflux-origin の状態文法へ適用し、CAS・単一 pending・ledger 外 head anchor・予算注入を一つの leaf 契約に閉じる点である。

D121 が固定した P3 は四性質だが、cap-lift や formal consumer は別条件である（`docs/decisions.md:5842-5854`）。本計画は「P3 を充足した」とは名乗らず、`MAX_APPROVED_GENERATIONS = 1` も変更しない。

### 親 brief (P1)〜(P4) の採否

| provisional | 判定 | 修正内容 |
|---|---|---|
| (P1) tracked registry を anchor にする | **修正採用** | registry の committed head と ledger を照合し、registry が健全な限り ledger の欠落・古い tail を fail-closed にする。ただし registry は同一 UID から保護されず、協調改竄は検出不能。Git tracking は監査可能性であって認証ではない（`brief.md:32-35`、`README.md:335-344`）。 |
| (P2) in-flight は予約 slot 1 件 | **修正採用** | `pending_slot is None` を唯一の予約可能条件にする。slot に nullable な `batch_commitment_sha256` を残し、後続 P4 の batch freeze を閉ざさないが、cardinality や seal 非公開は本 leaf では証明しない（`brief.md:35-36`、設計本文 `:232-233`）。 |
| (P3) 新 leaf、consumer 未結線 | **採用** | leaf 内契約だけを実装する。`WAL_STAGES` と `layer3_report.py` は変更しない。未知 stage と架空 variant の問題は設計本文 `:318-331` のまま裁定候補に残す。 |
| (P4) caller 注入の immutable budget policy | **修正採用** | frozen policy に I/Q/K を必須引数として持たせ、registry はその digest を束縛する。制約 tuple も必須で、欠落時の `0`/`None` fallback は置かない（`brief.md:40-41`）。 |

## 1. 新規 leaf と API

### ファイル構成

既存ファイルは編集しない。

- `orchestrator/campaign/reflux_origin_ledger.py:new L1-L760`
- `orchestrator/tests/test_reflux_origin_ledger.py:new L1-L680`

テスト末尾に実際に pytest を起動する `__main__` を置くため、`orchestrator/tests/README.md` の pytest-only allowlist は編集不要である（同 README `:105-126`）。`model.py`、`wal.py`、`layer3_report.py`、`__init__.py` にも変更を入れない。

実 production registry file は本 wave では追加しない。固定相対 path と schema のみ leaf に定義し、テストは `tmp_path` 内に authority fixture を作る。実 registry が無ければ API は fail-closed となる。実ファイル追加が必要なら、成果物 2 本という brief の境界を越えるため段 4 の裁定候補にする。

### 予定 line map

| planned lines | 内容 |
|---|---|
| `reflux_origin_ledger.py:new L1-L45` | schema/version、固定 registry 相対 path、64hex、size/frame 上限 |
| `L46-L105` | 専用例外階層 |
| `L106-L235` | frozen policy/layout/event/state/receipt 型 |
| `L236-L325` | canonical JSON、request/event/state digest |
| `L326-L485` | event schema と replay FSM |
| `L486-L590` | symlink 拒否、read-once、flock、短い write、fsync、tail scan |
| `L591-L675` | registry replay、head anchor、prepared/committed transaction |
| `L676-L760` | public `policy_sha256`、`replay_origin`、`commit_event` |
| `test_reflux_origin_ledger.py:new L1-L90` | fixture、独立 canonical golden、authority registry fixture |
| `L91-L235` | 型・policy・event 文法 |
| `L236-L345` | 単一 pending・CAS・実 process race |
| `L346-L485` | 4 crash 窓・二相 commit・idempotence |
| `L486-L610` | torn tail・削除・rollback・registry 改竄 |
| `L611-L680` | symlink/size/fsync と `__main__` |

### 公開 API 骨格

```python
REGISTRY_RELATIVE_PATH = PurePosixPath(
    "orchestrator/campaign/reflux_origin_registry_v1.jsonl"
)

@dataclass(frozen=True)
class OriginLedgerLayout:
    repository_root: Path
    ledger_root: Path

@dataclass(frozen=True)
class QueryFloorConstraint:
    base: int
    per_round: int
    rounds: int
    evidence_min: int

@dataclass(frozen=True)
class OriginBudgetPolicy:
    imax: int
    qmax: int
    kmax: int
    constraints: tuple[QueryFloorConstraint, ...]

@dataclass(frozen=True)
class OriginEvent:
    event_type: str
    operation_id: str
    slot_id: str | None = None
    iteration_index: int | None = None
    batch_commitment_sha256: str | None = None
    query_sha256: str | None = None
    constraint_sha256: str | None = None
    source_ref_sha256: str | None = None
    result: str | None = None
    result_ref_sha256: str | None = None
    disclosed_class_sha256s: tuple[str, ...] | None = None

@dataclass(frozen=True)
class OriginState:
    phase: str
    event_count: int
    head_event_sha256: str
    state_commitment: str
    iterations_used: int
    queries_used: int
    disclosures_used: int
    constraint_count: int
    constraint_set_sha256: str
    pending_slot_id: str | None
    pending_query_sha256: str | None
    pending_constraint_sha256: str | None
    last_iteration_index: int | None

@dataclass(frozen=True)
class EventReceipt:
    operation_id: str
    event_index: int
    event_sha256: str
    resulting_state_commitment: str
    current_state_commitment: str
    replayed: bool

def policy_sha256(policy: OriginBudgetPolicy) -> str: ...

def replay_origin(
    layout: OriginLedgerLayout,
    *,
    origin_id: str,
    budget_policy: OriginBudgetPolicy,
) -> OriginState: ...

def commit_event(
    layout: OriginLedgerLayout,
    *,
    origin_id: str,
    budget_policy: OriginBudgetPolicy,
    expected_state_commitment: str,
    event: OriginEvent,
) -> EventReceipt: ...
```

`origin_id` は caller が渡す不透明な lowercase 64hex とし、leaf は preimage・5-bit mask・provider/session を計算しない。

### 例外階層

```text
OriginLedgerError(ValueError)
├── OriginPolicyError
├── OriginSchemaError
├── OriginStateError
│   ├── OriginCASMismatch
│   ├── OriginReplayConflict
│   └── OriginBudgetExceeded
├── OriginIntegrityError
│   ├── OriginFramingError
│   ├── OriginChainError
│   └── OriginAnchorError
└── OriginDurabilityError
```

`OriginDurabilityError` は `phase/path/total_bytes/written_bytes/cause` を保持する。frozen dataclass と exact `type(...) is int` 検査は `reservation.py:26-55,202-207`、専用 error に既存 record/path を載せる形は `campaign_claim.py:13-25` を踏襲する。

## 2. on-disk 形式

### layout

```text
<repository_root>/
└── orchestrator/campaign/reflux_origin_registry_v1.jsonl  # tracked authority + heads

<ledger_root>/                                             # caller 注入
├── <origin_id>.jsonl
└── <origin_id>.tail-repair-*.json                         # 必要時だけ
```

`repository_root` と `ledger_root` は既存 directory の absolute `Path` を必須とする。機械固有 path を leaf に固定しない方針は `durable_root.py:2-5,20-42` に合わせる。

registry の相対 path は固定し、全 ancestor・final component の symlink を拒否する。regular file、size 上限、単一 fd からの read-once、duplicate key、exact schema を検査する。これは `claude_transport.py:282-339` の committed policy reader を踏襲する。ただし leaf 自身は `git ls-files` を実行せず、「同 path が本当に tracked か」は deployment/将来 consumer の義務とする。

### ledger record

各物理 record は canonical JSON object 1 個と LF 1 byte。再帰的に key を辞書順にし、

```python
json.dumps(
    value,
    sort_keys=True,
    ensure_ascii=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8") + b"\n"
```

で frame 化する。最終 object の key 順は次になる。

```json
{
  "event_index": 0,
  "event_sha256": "<64hex>",
  "event_type": "origin-opened",
  "operation_id": "<64hex>",
  "origin_id": "<64hex>",
  "payload": {
    "authorization_registry_sha256": "<64hex>",
    "budget_policy_sha256": "<64hex>",
    "manifest_sha256": "<64hex>"
  },
  "previous_event_sha256": "0000...0000",
  "previous_state_commitment": "<64hex>",
  "request_sha256": "<64hex>",
  "schema_version": "reflux-origin-ledger-event/v1"
}
```

- `event_sha256` は同 object から `event_sha256` だけを除いた canonical bytes の SHA-256。
- genesis の `previous_event_sha256` は `"0"*64`。
- `request_sha256` は `{schema, origin_id, operation_id, event_type, semantic payload, expected_state_commitment}` の digest。ordinal や current head は含めないため、crash 後も同じ request を再構成できる。
- registry の prepared record は、digest 済み全 ledger frame の `frame_sha256` も保持する。
- timestamp は入れない。CAS/idempotence に不要な非決定値と side channel を増やさない。

T-126 の index/previous/event digest は踏襲する（`attempt_ledger.py:23-32,192-207`）。一方、同実装の create-only 連番 JSON file (`:312-373`) は採らず、要求された単一 ledger file にする。

### state commitment

ledger head digestだけでなく、次の canonical state preimageを domain-separated SHA-256 する。

```text
schema/version
origin_id
authorization_registry_sha256
budget_policy_sha256
head event index + event_sha256
phase
iterations_used / queries_used / disclosures_used
constraint_count + sorted constraint set の digest
pending slot/query/constraint
last_iteration_index
```

これを caller CAS 値と registry の committed head に使う。constraint の実値集合は public state に出さず、件数と集合 digest だけを載せる。

### registry schema と head の場所

registry 自体も canonical JSONL + global hash chain とする。各 record の envelope は exact に次の key を持つ。

```text
schema_version
registry_index
previous_registry_sha256
record_type
origin_id
payload
registry_sha256
```

record type は ledger の 7 event とは別の内部 transaction 文法である。

| registry record | payload |
|---|---|
| `origin-authorized` | `manifest_sha256`, `budget_policy_sha256`, `ledger_name`。authority が事前配置し、leaf は発行 API を公開しない |
| `head-prepared` | `operation_id`, `request_sha256`, `expected_state_commitment`, `event_index`, `event_sha256`, `frame_sha256` |
| `head-committed` | prepared record digest、`event_index`, `event_sha256`, `resulting_state_commitment` |

head commitment の権威は最新 `head-committed.payload.resulting_state_commitment`。`origin-authorized` だけの状態では、同 registry record digest から authorized-state commitment を導出する。

書込み順は registry flock を保持したまま次の順に固定する。

1. ledger/registry を完全 replayし、CAS・予算・遷移を検査。
2. `head-prepared` を registry へ追記し `fsync(registry)`。
3. ledger frame を追記し `fsync(ledger)`、新規 file なら ledger root も fsync。
4. `head-committed` を registry へ追記し `fsync(registry)`。
5. registry parent directory を fsyncしてから成功を返す。

### `wal.py` との対比

| 項目 | 踏襲／変更 |
|---|---|
| append 前の frame 自己検査 | `wal.py:301-307` を踏襲。拒否 event は file/directory side effect 前に落とす |
| `O_APPEND|O_NOFOLLOW|O_CLOEXEC`、regular file、flock、LF tail gate | `wal.py:310-330` を踏襲 |
| short write loop、file fsync、directory fsync | `wal.py:332-380` を踏襲 |
| LF JSON frame | 踏襲。ただし WAL は record key を insertion order で書く (`wal.py:252-256`) のに対し、本 leaf は全階層を `sort_keys=True` に固定 |
| hash chain | WAL は明示的に持たない (`wal.py:14-15`)。本 leaf は event/global registry の二本に chain を持つ |
| tail scan/digest/repair receipt | `wal.py:398-465,468-512` を踏襲 |
| tail 修復条件 | WAL の「最後の LF まで戻す」より厳しくし、durable `head-prepared` が示す全 frame の正確な prefix の場合だけ修復。無関係な tail は fail-closed |
| state machine/CAS | WAL の一 record append から意図的に変更し、replay・予算・CAS・prepare/ledger/commit を同じ registry flock 内に含める |

## 3. event 文法と状態機械

### payload

| event | exact payload | 補足 |
|---|---|---|
| `origin-opened` | authority digest、manifest digest、budget policy digest | caller payload ではなく registry/policy から leaf が組む |
| `slot-reserved` | `slot_id`, `iteration_index`, `batch_commitment_sha256` | batch digest は nullable。値を proof と名乗らない |
| `query-bound` | `slot_id`, `query_sha256` | query は opaque digest |
| `constraint-added` | `slot_id`, `query_sha256`, `constraint_sha256`, `source_ref_sha256` | mask や anomaly 本文を leaf は解釈しない |
| `query-result` | `slot_id`, `query_sha256`, `result`, `result_ref_sha256` | `result` は `accepted|rejected` の二値 |
| `slot-tombstoned` | `slot_id` | reserved だが未 bound の slot に限定 |
| `origin-sealed` | sorted unique `disclosed_class_sha256s` | 公開自体は seal 後。ここでは公開予定集合を先に commit |

7 event は設計本文 `:306-314` と同一であり、追加の ledger event は作らない。

### 遷移表

| 現状態 | 許可 event | 次状態 | 主な拒否 |
|---|---|---|---|
| `AUTHORIZED` | `origin-opened` | `IDLE` | 他 event、二重 open |
| `IDLE` | `slot-reserved` | `RESERVED` | budget 超過、使用済 slot、iteration 飛越し |
| `IDLE` | `origin-sealed` | `SEALED` | disclosure 数が Kmax 超過 |
| `RESERVED` | `query-bound` | `BOUND` | slot 不一致、二重 bind |
| `RESERVED` | `slot-tombstoned` | `IDLE` | slot 不一致。I/Q は返却しない |
| `BOUND` | `constraint-added` | `CONSTRAINED` | query/slot 不一致、既出 constraint |
| `BOUND` | `query-result` | `IDLE` | query/slot 不一致 |
| `CONSTRAINED` | `query-result(result="rejected")` | `IDLE` | accepted、二重 constraint、tombstone |
| `SEALED` | なし | — | exact-idempotent retry 以外の suffix 全て |

同じ `operation_id` の exact retry は遷移判定前に既適用として返す。同じ key で request digest が違えば `OriginReplayConflict`。

iteration は最初を 0 とし、次の reservation は直前と同じ index、または `+1` のみ許す。新しい index の初出で I を 1、全 reservation で Q を 1 消費する。これにより同一 iteration 内の複数 query を表現でき、Imax と Qmax が同義化しない。

### 単一 in-flight の述語

replay 中、各 prefix で次を強制する。

```text
pending =
  slot-reserved の slot 集合
  − 同じ slot の query-result / slot-tombstoned 集合

len(pending) ∈ {0, 1}
```

さらに、

```text
phase == IDLE       ⇔ len(pending) == 0
phase in RESERVED/BOUND/CONSTRAINED ⇔ len(pending) == 1
```

とし、pending slot ID に対する全中間 event の一致を要求する。`slot-reserved` の前提は常に `pending is None`。slot ID は一度 terminal になっても再利用不可である。

## 4. CAS

caller は `replay_origin()` または直前の `EventReceipt` から得た `state_commitment` を、次の `commit_event(expected_state_commitment=...)` に必ず渡す。省略値はない。

registry の排他 flock を取得した後、ledger と registry を再読・replayして actual commitment を作り、exact 64hex 比較する。不一致なら prepare record を含め一 byte も書かず `OriginCASMismatch(expected, actual)`。

flock と CAS の分担は次のとおり。

- flock: 同時に critical section に入る協調 writer を直列化し、tail gate・replay・registry/ledger/fsync の物理操作を守る。既存 context manager の基本形は `lock.py:41-64`。
- CAS: actor が lock 取得前に読んだ状態と、取得後の現 head が同一かを検査する。
- flock だけでは、A が state S を読んだ後、B が S→T を commitし、B の lock 解放後に A が取得して「S を前提とした event」を T へ適用する stale decision を防げない。
- いずれも非協調 writer、別 registry path、同一 UID の直接改竄を防ぐ認証機構ではない。

## 5. crash replay

### 論理 crash 窓

| crash 窓 | replay 後の正規状態 | 再開 |
|---|---|---|
| reservation 後・provider 前 | `RESERVED(slot=S)`、I/Q は消費済み | 同じ reservation operation の replay は no-op。次は `query-bound(S, …)` または provider 未開始を確認できない場合の `slot-tombstoned(S)`。自動 refund はしない |
| verifier red 後・`constraint-added` 前 | `BOUND(slot=S, query=Q)` | 同じ verifier evidence ref を用いて `constraint-added` を replayする。evidence が無ければ結果を捏造せず pending のまま fail-closed |
| `constraint-added` 後・`query-result` 前 | `CONSTRAINED(S,Q,C)` | 同じ constraint operation は no-op。その後 `query-result(result="rejected")` だけを許す |
| query 完了後・seal 前 | `IDLE` | 同じ result operation は no-op。残 slot を予約するか `origin-sealed` を commit |

provider 呼出回数や verifier evidence の永続化は P5/consumer 側であり、この leaf は呼出しを再実行しない。

### 物理 write crash

`head-prepared → ledger frame → head-committed` の各 durable 境界から次のように回復する。

| disk 状態 | 回復 |
|---|---|
| prepared 有、ledger は旧 head | 同じ `(origin_id, operation_id, request_sha256)` の call だけが予定 frame を追記 |
| prepared 有、ledger tail が予定 frame の厳密 prefix | repair receipt を O_EXCL 作成し file/dir fsync後に tail を切断、同じ frame を再追記 |
| prepared 有、ledger frame 完全、commit 無 | frame/event/state digest を照合し、registry commit だけ追記 |
| commit 完全 | exact retry は既存 receipt を返し bytes 不変 |
| prepare 無の torn tail、または予定 frame と異なる tail | 自動修復せず `OriginFramingError` |

repair receipt を truncate より先に耐久化する順序は `wal.py:496-508` およびその検査 `test_campaign.py:1084-1135` を踏襲する。

### idempotent key

同一性 key は `(origin_id, operation_id)`。同じ key で `request_sha256` が一致すると既適用 event の ordinal・digest・その prefix の state commitment を返す。不一致は必ず拒否する。

二重適用が起きない根拠は三重である。

1. replay が origin 内の operation ID 重複を拒否する。
2. lookup・CAS・append が同じ registry flock 内。
3. registry prepared record が予定 ordinal・previous state・全 frame digest を固定し、crash 後に別 bytes を同じ transaction として完成できない。

## 6. 削除耐性の主張上限

| 操作 | registry が保持される場合 | 検出不能な境界 |
|---|---|---|
| (a) ledger file 全削除 | `origin-opened` 以降の committed head が非 genesis なのに file が無いため `OriginAnchorError`。予算 reset ではなく使用不能 | registry も整合的に書き換えた同一 UID 攻撃。authorization のみで未 open の origin と、authority 自体の偽造 |
| (b) 古い ledger へ rollback | ledger head/index/state commitment が registry committed head より古く、拒否 | registry も同じ時点へ協調 rollback された場合 |
| (c) 中間 record 削除 | index 連番または `previous_event_sha256` が破れ、registry 照合前に拒否 | suffix の hash と registry を全て再計算する同一 UID 攻撃 |
| (d) registry 自体の改竄 | duplicate key、非 canonical、hash-chain 切断、prepare/commit 不整合、ledger との head 不一致は拒否 | 内部整合する全面書換え、registry+ledger の協調 rollback、Git metadata/checkout ごとの置換 |

registry path 自体が無ければ API は fail-closed だが、それだけでは「削除を検出した」とは言わない。未配置 checkout と削除後を leaf 単独では区別できないためである。

同様に、Git diff が改変を可視化しうることと、同一 UID の caller に対する改変防止・真正性証明は別である。設計本文も「WAL 最終 SHA は外部 anchor なしに全面改竄を防がない」としている（`:341-342`）。

## 7. 予算の後差し

`OriginBudgetPolicy` は次を満たす。

- `imax/qmax/kmax/constraints` は全て必須 positional-free keyword。default を置かない。
- exact `int` を要求して `bool` を拒否する。
- I/Q/K は明示された非負値のみ許す。明示的な 0 は「origin を開いて seal はできるが該当操作は一件もできない」という政策値であり、欠落値の代用品ではない。
- registry の `origin-authorized` が canonical policy digest を束縛し、caller の policy drift を file I/O 前に拒否する。
- `dict.get("Qmax", 0)`、`None = unlimited`、空 policy の暗黙許可は実装しない。
- reservation 時に prospective count を検査し、超過 event は provider 等へ到達する前に無効果で拒否する。
- tombstone/reject/crash 後も予約済み Q/I を減らさない。
- seal 時の sorted unique disclosure refs の件数を Kmax で検査する。

U4 の式は値ではなく次の immutable constraint として後差しできる。

```python
QueryFloorConstraint(
    base=1,
    per_round=32,
    rounds=R,
    evidence_min=E_min,
)
```

検査は `qmax >= base + per_round * rounds + evidence_min`。係数や R/E_min を leaf の科学的既定値として持たず、policy bytes と digest に含める。現在は `constraints=()` を caller が明示できるが、式を採用した authority record では constraint を抜いた policy は digest mismatch となる。

## 8. テスト vector

記号は S=単一 in-flight、C=CAS、R=crash replay、D=削除耐性。

| vector | 性質 | 非退化 assert と既存との差 |
|---|---|---|
| V1 canonical frame golden | C/D | 手書き literal bytes と固定 SHA を照合し、key 順・LF・digest field を固定。WAL は hash chain を持たない (`wal.py:14-15`) |
| V2 全 valid path と全 forbidden transition | S/R | 7 event の full sequence、各 state から他 6 event を拒否。origin event は既存テストに無く、erratum も T-126 とは state が違うと訂正している (`brief-erratum-1.md:24-32`) |
| V3 sequential double reserve | S | slot A pending 中の slot B を正しい現 CAS でも拒否し bytes/head 不変。claim の one-shot 所有検査 (`test_campaign_claim.py:43-78`) とは別 |
| V4 二実 process の異なる reserve race | S/C | 同一 expected commitment、異なる op/slot で開始 barrier。成功 1・CAS mismatch 1・pending 1 を要求。既存 process race は claim file の winner だけ (`test_campaign_claim.py:86-145`) |
| V5 stale CAS after lock handoff | C | A commit 後に B が旧 commitment を渡して拒否、registry prepare も増えない |
| V6 idempotent old-operation replay | C/R | event A、後続 B の後で A を再送して ledger bytes 不変。同じ op ID・別 payload は conflict。T-126 の exact-idempotent idiom (`attempt_ledger.py:344-473`) を reflux event 列で独立固定 |
| V7 pending predicate prefixes | S | 各 frame prefix を replayし pending count が常に 0/1。最終状態だけを見るテストにしない |
| V8 四つの論理 crash window | R | 上記四状態を各々 file fixture として再起動し、許可される唯一の継続と no-refund を検査 |
| V9 prepare/ledger/commit fault matrix | R/C | 各 fsync 境界で例外注入し、再送後 frame 1 件・commit 1 件・同じ receipt。既存 WAL repair は二 file transaction を扱わない |
| V10 short write・zero progress・fsync 順 | R | registry/ledger 双方で short write 完遂、zero progress 拒否、prepare fsync < ledger fsync < commit fsync を記録 |
| V11 prepared frame の torn tail | R/D | 全 byte offset の代表値で exact prefix だけ repair。1 byte 異なる tail は拒否。既存 WAL は generic tail repair (`test_campaign.py:1030-1081`) |
| V12 ledger missing/rollback/intermediate delete | D | registry bytes を固定したまま ledger だけ三種変異し、missing/head mismatch/chain mismatch を別 error で拒否 |
| V13 registry tamper matrix | D | duplicate key、middle delete、prepared/commit 不一致、registry-only rollback は拒否。registry+ledger 協調 rewrite は「検出不能残余」の確認用で、成功を耐性証明に数えない |
| V14 budget missing/zero/boundary/formula | S 補助 | missing 3 key、bool、Qmax-1/Qmax、tombstone no-refund、U4 floor の境界を検査。既存 reservation は walltime/job binding (`test_reservation.py:50-134`) で query/iteration policy ではない |
| V15 registry/ledger path safety | D | registry ancestor/final symlink、ledger symlink、oversize/read-once short read を拒否。既存 transport policy reader (`claude_transport.py:282-339`) の別 schema なので新 vector が必要 |
| V16 batch seam | S 補助 | `batch_commitment_sha256=None` と異なる二つの 64hex が同じ slot 文法で保存可能なことだけを検査し、batch=1 や freeze 完了を真と assert しない |

### 恒真になりうる vector と是正

1. **実装の encoder で期待 bytes と digest を作る。**  
   同じ key 取り違えを双方が共有して恒真になる。期待値は手書き canonical literal と固定 SHA にし、実装 helper を期待値生成に使わない。

2. **ledger を rollback した後、同じ実装で registry head も作り直す。**  
   anchor を攻撃対象と一緒に更新するため必ず整合する。V12 では registry bytes を mutation 前に固定し、ledger だけを変える。協調改竄は別の「検出不能残余」vector に隔離する。

3. **race の二 worker が同一 operation ID・同一 payload を使う。**  
   両方成功しても単なる idempotenceであり、単一 pending/CAS の競合を撃たない。異なる operation ID と slot ID、同一 expected commitment を使う。

4. **origin/query/constraint digest を全て `"a"*64` 一種類だけで試す。**  
   field swap を検出できない。最低二つの相異なる 64hex を使い、query と constraint を交換した record が schema/state test で落ちることを確認する。

## 9. 却下案

1. **flock だけで単一 writer を名乗る。**  
   同時 write は直列化できても、lock 取得前の stale decision を防げないため CAS 不在となる。

2. **head digest を ledger 最終行だけに置く。**  
   ledger 全削除や古い prefix への置換で head ごと消え、予算が新品に戻る。ledger 外 registry head が必要。

3. **任意の unterminated tail を WAL と同じく無条件切断する。**  
   prepared transaction と無関係な改竄まで crash として消せる。予定 frame の厳密 prefix だけに限定する。

4. **I/Q/K の欠落を 0 または unlimited にする。**  
   0 は実質的な即枯渇、`None` は無制限になり、未裁定値を既定政策へ変えてしまう。

5. **`orchestrator/qualification.attempt_ledger` を直接 import／共有化する。**  
   良い idiom はあるが、qualification 固有 capability・lineage・event state・create-only 連番 file である（`attempt_ledger.py:2,312-373`）。別 package の編集や一般化は「新規 leaf に閉じる」を越える。hash/envelope/二相化だけを再実装する。

6. **`WAL_STAGES` に `reflux-control` を追加して leaf の有効性を示す。**  
   `layer3_report.py` が未知 stage を拒否し、commit 無し固定 variant を棄却候補として数えるため、stage だけの追加は正式 report を壊す（設計本文 `:318-331`）。

7. **tracked registry なら同一 UID 改竄も検出できると主張する。**  
   tracked は review/audit の面を作るだけで、署名・別 UID・外部 service ではない。主張過大なので却下する。

## 総括

実装の核は、canonical hash-chain ledger と append-only tracked registry の `prepare → ledger → commit`、その committed state commitment を使う CAS、prefix ごとの厳密 FSM である。pending は予約 slot 最大 1、event replay は `(origin_id, operation_id)`、予算は digest 束縛された必須 frozen policy として後差しする。既存 consumer、P1/P5 面、cap は非接触とする。

確信を持てなかった点は二つある。第一に、裁定済みなのは「tracked registry から始める」までで、runtime ごとに同 tracked JSONL へ head を追記し、その差分をいつ commit/fold するかは資料に無い。本計画は rollback 検出に必要な最小形として runtime append を選んだため、段 3/4 で運用面を攻撃すべきである。第二に、実 registry file を本 wave の三つ目の成果物として追加してよい根拠が無いので追加しない案とした。そのため leaf はテスト可能だが、authority record が別途置かれるまでは production で fail-closed に使用不能である。

pytest・ビルドは実行しておらず、以上は指定資料と関連先行実装の静的読取りに基づくプランである。