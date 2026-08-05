# T-401 racct 欠測の恒久対応 — 設計起草レポート

参照略号: `RP` = [run_probes.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/driver/run_probes.py:1)、`SO` = [signal_observer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/driver/signal_observer.py:1)。行番号は現 worktree で再確認した。静的読取りのみで、pytest・scheduler command・probe 再実行はしていない。

### 1. 現状の機構の正確な記述

結論から言えば、`.e` の NQSV block はすでに「終端原因」と「終端実証」の証拠だが、`accounting_available` / `accounting_integrity_valid` を生成する正式会計 snapshot ではない。正式会計 snapshot は `racctjob` と `racctreq` の組だけである。

| field | materialize と値域 | 判定への効果 |
|---|---|---|
| `accounting_available: bool` | `racctjob` と `racctreq` の双方で record が存在するときだけ `true`。集約式は `all(validation.available)` (`RP:1792–1817`)。`accounting_evidence` は同値を強制される (`RP:294–300, 407–415`)。 | `observation_valid` の直接項ではない。非 signal leg では racct cause の選択、終端証拠の racct 分岐へ間接的に効く。`.e` が存在してもこの field は `true` にならない。 |
| `accounting_integrity_valid: bool \| null` | record が存在して非 0 rc・件数不一致・provenance 不成立等なら `false`、両 command が available かつ valid なら `true`、純粋な欠測なら `null` (`RP:1802–1817`)。 | `false` だけが `observation_valid` を落とす。`null` は欠測として通る (`RP:396–400`)。available なのに `null` は malformed とされ `false` へ強制される (`RP:376–383`)。 |
| `termination_cause_consistent: bool \| null` | まず有効な `qwait` が必要。signal leg は manifest-bound `.e` の signal/Remaining Elapse と `finally_exit` を使う。非 signal leg は racct、欠測時は `.e` を使う (`RP:2764–2853`)。 | `false` だけが `observation_valid` を落とし、`null` は通る。signal leg では必要な `.e` mechanics が無ければ実質 `false` になる。 |
| `observation_valid: bool` | base observation predicates の全真に、`accounting_integrity_valid is not False` と `termination_cause_consistent is not False` を加えた値 (`RP:396–400`)。attempt-result と wave state に保存される (`RP:4023–4026, 5425–5443`)。 | 観測 gate。本 field 単独では authoritative にならない。互換 field `admissible` は現在これの alias (`RP:3093, 5450`)。 |
| `terminal_proven` | 実在する canonical 名は wave state の `external_root_terminal_proven: bool` (`RP:4003–4025`)。attempt-result では `external_root_terminal_proof.valid` という nested 値であり、top-level `terminal_proven` はない (`RP:5344–5368, 5420`)。 | authoritative 選出のもう一方の独立 gate。`observation_valid` とは別に計算される。 |

正式 racct validator `_accounting_valid` の実際の条件は次のとおりである (`RP:1649–1762`)。

1. `exact_request_record_count_valid`: **stdout 中の Request ID record 数**が `expected_records` と一致する (`RP:1680–1683`)。
2. `exclusive_request_ids_valid`: stdout/stderr の全 Request ID が期待 ID だけである (`RP:1684–1688`)。
3. `Started Request Time` が stdout にある (`RP:1720`)。
4. `Ended Request Time` が stdout にある (`RP:1721`)。
5. `Elapse` が stdout にある (`RP:1722`)。

さらに上の五つだけではなく、invalid ID と cause line の request 束縛を含む `stream_provenance_valid` も `valid` の必要条件である (`RP:1690–1715, 1723–1730`)。`racctjob` の期待件数は `leg.nodes`、`racctreq` は 1 である (`RP:1765–1789`)。

依存関係を式にすると以下になる。

```text
A = racctjob.available ∧ racctreq.available

I =
  false  if present record に rc/件数/ID/provenance/Started/Ended/Elapse 違反あり
  true   if A かつ両 command が valid
  null   if 純粋な欠測

O = all(base_observation_predicates)
    ∧ (I is not false)
    ∧ (termination_cause_consistent is not false)

T_normal =
  request_id_available
  ∧ request_not_active_at_controller_stop
  ∧ (
       qwait_terminal_receipt_valid
       ∨ racct_snapshot_valid
       ∨ (.e_valid ∧ qstat_request_absent)
     )

T_resolve =
  saved_qsub_receipt_valid
  ∧ qstat_request_absent
  ∧ (
       qwait_terminal_receipt_valid
       ∨ valid_racct_command
       ∨ .e_valid
     )

authoritative = O ∧ external_root_terminal_proven
```

通常経路の終端論理は `RP:5331–5368`、resolve は `RP:4591–4645`、authoritative の最終式は `RP:329–342`、first-authoritative 固定は `RP:4041–4045` にある。

したがって現在の効果範囲は次のとおりである。

- racct の純粋な permission 欠測は `accounting_available=false`, `accounting_integrity_valid=null` となり、それだけでは観測を無効にしない。
- racct record が存在して壊れていれば `accounting_integrity_valid=false` となり、観測を無効にする。
- `.e` は `termination_cause_consistent` と終端 path 3 へ効くが、`accounting_available` / `accounting_integrity_valid` へは効かない。
- `rbudgetcheck` は hygiene・費用・transaction completion に効くが、正式会計 fields へは流れない (`RP:2928–2937, 3118–3156, 5512–5559`)。
- authoritative 選出は D161 の記述どおり `observation_valid ∧ external_root_terminal_proven` だけである。[D161:7970–7999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/docs/decisions.md:7970) と実装は一致する。

なお driver README の「全 `validity_conjunction` が true のときだけ admissible」「最初の admissible が authoritative」という説明 (`README.md:127–131`) は旧モデルの記述であり、現コード・D161 より古い。

### 2. 会計証拠の供給源の棚卸し

保存済み SHA-256 は「capture 後の bytes が変わっていない」ことを検査するもので、producer の認証ではない。特に全 evidence は最終的に実行 user が書ける領域にあり、root 署名や scheduler 署名はない。その中でも、login-side command の live pipe は job body から独立している一方、`.e` は job と scheduler の共有 stream である。

| 供給源 | (a) 取得可否の実測 | (b) 粒度 | (c) 信頼境界 | (d) 現在の取得・保存・用途 |
|---|---|---|---|---|
| `racctjob -I` | 現 brief の実測は rc=1、header のみ、stderr は sudo password gate。既存 evidence でも [commands.jsonl:37–41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260804T125421Z-5e03df98c93b444e/attempts/t362-mitigation/20260804T125421Z-t362-mitigation-a1-2a754178cd1a19d9/work/controller/commands.jsonl:37) が rc=1、[stderr:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260804T125421Z-5e03df98c93b444e/attempts/t362-mitigation/20260804T125421Z-t362-mitigation-a1-2a754178cd1a19d9/work/controller/raw/00035-final-racctjob-attempt-1.stderr.raw:1) が同じ marker。 | job 単位。期待件数は `leg.nodes`。 | scheduler accounting DB を sudo wrapper 経由で読む想定。job body は live stdout pipe を書けない。保存 file/ledger は controller user が書くため、暗号学的な第三者証明ではない。 | controller が最大5回取得 (`RP:1765–1789`)。signal observer も取得するが、こちらは permission 判定で初回停止済み (`SO:689–700, 861–875`)。raw・argv・rc・hash は Recorder が保存 (`RP:1058–1124`)。 |
| `racctreq -I` | `racctjob` と同じ permission gate。 | request 単位、期待 record 1件。 | 同上。 | `racctjob` と対でのみ `accounting_available=true` になる (`RP:1797–1854`)。片方だけでは正式 snapshot は available にならない。 |
| `.e` の NQSV accounting block | 取得可能。実ファイルは Request ID、Number of Jobs、Started/Ended、Elapse 等を持つ ([meas-feasibility.sh.e889948:3–14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/meas-feasibility.sh.e889948:3))。2-job 実例は 1 ファイルだけが `Number of Jobs: 2` の request block を持ち (`stderr.raw:3–14`)、もう1ファイルは size 0 ([manifest:23–39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260803T150807Z-5809d1d8d4d2f8c5/attempts/t361-flock/20260803T150808Z-t361-flock-a1-9060899fb1686d87/work/controller/job-output-manifest.json:23))。 | request 単位。`Number of Jobs: N` は総数 field であり N 個の job record ではない。 | `qsub -e` が job stderr の出力先を同じ file にする (`RP:942–954`)。実 job script 自身も `>&2` へ書く ([signal_job_body.sh:41–55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/driver/signal_job_body.sh:41))。従って scheduler と job body の混合 stream であり、job は同形 block を生成できる。manifest/hash は origin を認証しない。 | 通常経路は rename 前の hash/size を manifest に保存 (`RP:2072–2116`)。parser は Request ID/Ended/cause を抽出 (`RP:1882–2069`)。現在は termination cause と `.e + qstat absence` の終端 path に使用 (`RP:2764–2853, 4616–4618, 5340–5343`)。 |
| `rbudgetcheck` | 現 brief では sudo なし rc=0。保存済み例も `SFC 307.72 ...` → `306.37 ...` (`rbudgetcheck-*.stdout.raw:4`)。 | group/project 単位。request/job へ束縛されない。 | 外部 budget service の live stdout を controller が捕捉するが、同じ group の並行 job 消費を分離できない。保存物自体は user-owned。 | qsub 前後と session/wave 前後に取得 (`RP:5121–5123, 5293–5294, 5585–5593, 5710–5734`)。`Decimal` 差分を保持するが換算は `UNDETERMINED` (`RP:3132–3156`)。会計 integrity には使わない。 |
| `qstat -J -f` | 取得可能。保存済み raw は Request ID、Batch Job Number、Execution Host に加え Memory/CPU Time 等の live resource counter を持つ ([qstat raw:1–18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260804T125421Z-5e03df98c93b444e/attempts/t362-mitigation/20260804T125421Z-t362-mitigation-a1-2a754178cd1a19d9/work/controller/raw/00013-lifecycle-qstat-attempt-1.stdout.raw:1))。終端後は `does not exist` ([qstat raw:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260804T125421Z-5e03df98c93b444e/attempts/t362-mitigation/20260804T125421Z-t362-mitigation-a1-2a754178cd1a19d9/work/controller/raw/00034-lifecycle-qstat-attempt-1.stdout.raw:1))。 | request 内の job 行を持つ live snapshot。終了後の request accounting ではない。 | scheduler service の direct response。job body は live pipe を書けないが、保存物は controller user が書く。 | bounded retry 付きで raw 保存し、visibility/state/hosts を解析 (`RP:1497–1528`)。観測の identity/lifecycle と `.e` 終端 path の不在確認に使用。resource counter 自体は未解析。 |
| `qwait` receipt | 取得可能。mitigation 実例は rc=9 と `ELAPSE time limit exceeded` ([commands.jsonl:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260804T125421Z-5e03df98c93b444e/attempts/t362-mitigation/20260804T125421Z-t362-mitigation-a1-2a754178cd1a19d9/work/controller/commands.jsonl:35)、[stderr:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260804T125421Z-5e03df98c93b444e/attempts/t362-mitigation/20260804T125421Z-t362-mitigation-a1-2a754178cd1a19d9/work/controller/raw/00003-qwait.stderr.raw:1))。 | request 単位の receipt。job別資源や exact signal 種別は持たない。 | scheduler service の direct response。exact argv と自然終了を controller が検査する。 | qsub 直後に background 起動 (`RP:5162–5172`)。request ID、timeout、controller termination、rc/text を検査 (`RP:2604–2685`)。観測 gate、termination cause の前提、終端 path 1 に使う。 |
| `qsub` receipt・persistent ledger・compute marker | 取得可能。 | request の宣言値と job identity。実消費 accounting ではない。 | qsub response は scheduler、期待 node 数は controller source、marker は job body が書く。 | expected `leg.nodes`、完全 argv、request ID、job number/host の拘束に使用 (`RP:933–959, 2128–2177, 5107–5158`)。`.e` の `Number of Jobs` を将来照合する補助にはなるが、job accounting record の代替ではない。 |

他に `qdel` receipt、`.o`、probe event、inventory が存在するが、いずれも会計量・Started/Ended/Elapse を供給しないため、正式会計源にはならない。

重要な実装上の例外として、`_saved_nqsv_stderr_accounting` は manifest entry だけでなく未改名 `*.e` も直接 glob する (`RP:1908–1912`)。後者は `manifest_bound=false` のままでも最終 `valid` が真になりうる (`RP:2028–2068`)。resolve はその `valid` を qstat 不在と組み合わせて採用する (`RP:4616–4618`)。従って「すべての `.e` 証拠が manifest-bound」という理解は正しくない。

### 3. 設計案 (択一)

以下の全案で、authoritative 式と F92 の終端三経路は緩めない。`Number of Jobs: N` を N 個の job record と読み替える案は成立案に数えない。それを行うと `_accounting_valid(expected_records=leg.nodes)` の exact-record 契約を別物へ変更するためである。

#### 案 A — racct を正式源のまま残し、permission だけ即時打切りする

**正式な会計証拠と field**

- 正式源: 現状どおり `racctjob + racctreq`。
- `accounting_available ∈ {true,false}`、`accounting_integrity_valid ∈ {true,false,null}`、`accounting_unavailable_reason ∈ {permission,empty,error,null}` を変更しない。
- `.e` は termination cause / terminal proof のまま。
- `_collect_accounting` は、1回目が「record 不在かつ permission marker」のとき、その command の残り4回を行わない。`empty` / transient `error` の retry は現状維持する。
- `REQUIRED_EXTERNAL_COMMANDS` は据置。各 attempt で両 command を1回は実行するため、permission policy の変化や異常 record を隠さない。

**五検査**

permission gate 下では record がないため、exact count / exclusive IDs / started / ended / elapse はすべて `null`（未評価）。racct が利用可能になった場合だけ、現行五検査をそのまま適用する。

**受理集合**

不変。現在の permission 出力に対し、5回同じ失敗を得ても1回で止めても最終値は `available=false`, `integrity=null`, `reason=permission` で同じである。各 attempt で再確認するため、環境変化時に本来検出される integrity failure を隠さない。

**凍結との整合**

- D161: 完全一致。
- erratum-1: permission marker を実際に観測して `permission` とするため一致。
- F92: `.e` の終端用途を変更しない。
- F92/F93 の gate 分離も維持 ([F92:2140–2146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/docs/failures.md:2140)、[F93:2150–2161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/docs/failures.md:2150))。

**実装量**

`_collect_accounting` の break 条件と receipt metadata、概ね **10¹行**。observer はすでに permission で即時停止するため基本的に変更不要。将来の fixture test は 10²行弱の規模。

#### 案 B — `.e` を「正式な request summary sidecar」にするが、D161 会計 fields へ入れない

**正式な会計証拠と field**

新しい情報証拠 object を追加する。

```text
nqsv_request_summary.schema = "nqsv-request-summary/v1"
nqsv_request_summary.available: bool
nqsv_request_summary.request_integrity_valid: bool | null
nqsv_request_summary.granularity = "request"
nqsv_request_summary.trust_class = "mixed-job-scheduler-stderr"
nqsv_request_summary.request_block_count: int
nqsv_request_summary.reported_number_of_jobs: int | null
nqsv_request_summary.reported_number_of_jobs_matches_leg_nodes: bool | null
nqsv_request_summary.started_present / ended_present / elapse_present: bool | null
```

既存 `accounting_available=false`, `accounting_integrity_valid=null`, `reason=permission` は維持する。案 A の permission 即時打切りも併用する。

**五検査**

- exact record count: request block exact-one は成立可能。ただし `expected=leg.nodes` 件の job record は**成立しない**。
- exclusive request IDs: 成立可能。
- started: 成立可能。
- ended: 成立可能。
- elapse: 成立可能。

`Number of Jobs` の一致は補助 cross-check であり、exact job records の代用とは記録しない。

**受理集合**

不変。sidecar は `observation_valid`、`terminal_proven`、authoritative 選出に入力しない。

**凍結との整合**

D161 の三分離と erratum-1 を変えず、F92 の `.e + qstat absence` も維持できる。信頼階層を field に明記するため P1 の問題は隠さない。ただし既存 `saved_nqsv_stderr_accounting` がすでに大半の情報を保存しており、成果物上の追加価値は小さい。

**実装量**

`_saved_nqsv_stderr_accounting`、attempt-result/wave-state materialization、sidecar schema を変更し、**10²行（約100–200行）**。

#### 案 C — `.e + qstat job roster + qwait` を mixed-trust composite 会計にする

**正式な会計証拠と field**

`.e` 単独ではなく、次の全構成を新しい正式源とする。

```text
accounting_source = "nqsv-composite-v1"
accounting_granularity = "request-with-job-roster"
accounting_trust_class = "mixed-job-scheduler-stderr+external-scheduler-receipts"
accounting_available: bool
accounting_integrity_valid: bool | null
```

完全な source は次を要求する。

- `.e` の exact-one request block
- qsub template・request-expanded filename・manifest/hash/size の拘束
- qstat raw から重複除去した `(request_id, Batch Job Number)` が exactly `leg.nodes`
- `.e` の `Number of Jobs == leg.nodes`
- request-bound natural `qwait`
- 現行の `termination_cause_consistent` も別 conjunct として維持

**五検査**

- exact record count: `.e` だけでは不成立。qstat の external job roster を併用して初めて成立。
- exclusive request IDs: `.e` と全 qstat row の双方で成立を要求。
- started: `.e` から成立。
- ended: `.e` から成立。
- elapse: `.e` から成立。

**受理集合**

同じか狭くなる。定義を `O_new = O_current ∧ composite_integrity_not_false` とし、composite を既存の false cause や terminal failure の救済には使わない。欠測は従来どおり `null`、矛盾だけ `false` とする。

**凍結との整合**

D161 の三分離と exact job count は維持できるが、job record の供給源を racct から qstat roster へ変える意味変更である。同じ `evaluation_model="split-v2"` のまま入れると semantic collision になるため、新 evaluation model と新しい decision が必要。F92 の `.e` 単独禁止は維持される。

ただし Started/Ended/Elapse の bytes は依然 job-writable stream 由来で、外部 DB と同格にはならない。

**実装量**

qstat job-row parser、composite validator、snapshot selection、schema/migration、保存経路で **2×10²～4×10²行**。

#### 案 D — root/admin 所有の scheduler export receipt を導入する

**正式な会計証拠と field**

管理側 collector が scheduler DB から request 1件と `leg.nodes` 件の job record を exportし、一般 user が書けない spool または署名済み receipt として渡す。

```text
accounting_source = "scheduler-export-v1"
accounting_granularity = "request+job"
accounting_authenticity_valid: bool
accounting_available: bool
accounting_integrity_valid: bool | null
```

**五検査**

- exact record count: `leg.nodes` 件の job record と request 1件を検査でき、成立。
- exclusive request IDs: 成立。
- started: 成立。
- ended: 成立。
- elapse: 成立。

**受理集合**

同じか狭くする。receipt は integrity の追加検査にだけ使い、既存の `.e` cause failure や terminal failureを上書きしない。receipt 欠測は従来どおり `null`、署名・owner・件数・因果矛盾は `false` とする。

**凍結との整合**

D161 の意図に最も忠実で、job-writable `.e` への信頼格下げもない。ただし新しい証拠権威・署名/owner 契約を decision として定める必要がある。F92 の終端三経路は変更しない。

**実装量**

driver 側の receipt loader/validator/source selection が **2×10²～4×10²行**。これとは別に管理側 collector と運用配線が少なくとも **10²～10³行級または同等の外部作業**となり、現権限だけでは完結しない。

### 4. 推奨と不採用理由

**推奨は案 A**である。すなわち、`.e` を既存の正式会計 fields へ昇格させず、racct の permission marker を1回確認した時点でその command の retry を打ち切る。

理由は三つある。

- `.e` は request summary であって、`expected=leg.nodes` 件の job record を供給しない。`Number of Jobs: N` を N records と読むことは D161/S4 の exact job count を別物へ変える。[S4:15–19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-04_t399-t400-signal-mitigation/s4-adjudication.md:15) は accounting 欠測だけを外し、件数・排他 ID・因果検査を残す裁定である。
- `.e` は job-writable で、manifest/hash は producer authenticity を与えない。既存の termination purpose には qwait/qstat との複合で使えるが、外部 accounting DB と同じ field 名で扱う根拠にはならない。
- 現在の authority は racct 欠測下でも成立済みであり、正式昇格による受理上の必要性がない。実例は `accounting_available=false`, `accounting_integrity_valid=null`, `termination_cause_consistent=true`, `observation_valid=true` である ([RESULT.md:13–20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-04_t399-t400-signal-mitigation/RESULT.md:13))。

他案を採らない理由は次のとおりである。

- 案 B: 証拠の説明力は増すが、既存 nested `.e` 解析結果と重複し、T-401 の死荷重以外に新しい保証を加えない。
- 案 C: job count を qstat で補えるが、終了時刻・Elapse は依然 mixed stream 由来である。schema/migration 費用に対して、現在の hazard conclusion の証拠強度向上が小さい。
- 案 D: 唯一 racct 相当の独立性を回復できるが、管理者権限と新しい運用面が必要で、危険 probe 専用 controller には過大である。将来「独立 scheduler DB accounting が必須」と裁定された場合の次善策とする。

併せて、どの案でも raw `*.e` が manifest-bound でなくても resolve path に入れる現状は別途閉じるべきである。少なくとも exact qsub template、request-expanded filename、expected file count を照合する変更は受理集合を狭めるだけであり、証拠強度を改善する。

### 5. 親 brief への反証

| 対象 | 判定 | 一次資料・コードとの照合 |
|---|---|---|
| P1 | **食い違いなし。むしろ brief より強い問題がある。** | `qsub -e` と job の `>&2` が同じ stream を共有する (`RP:942–954`, `signal_job_body.sh:41–55`)。加えて raw `*.e` の resolve path は manifest-bound を必須にしていない (`RP:1908–1912, 2068, 4616–4618`)。 |
| P2 | **「唯一の外部会計信号」は字義どおりには過剰。** | qstat raw に job 単位の Memory/CPU Time 等の external scheduler resource snapshot が実在する。ただし終了後に消え、Started/Ended/Elapse を持たず、現コードも解析しないため、request-bound final accounting の代替にはならない。`rbudgetcheck` が group 単位で request 束縛不能という結論自体は一致 (`RP:3098–3156`)。 |
| P3 | **主旨は一致、射程は過剰。** | `_collect_accounting` の sleep は 2 command × 4回 × 2秒 = **16秒**で正しい。ただし `request_id is not None` の attempt だけが対象 (`RP:5242–5290`)。signal observer は permission で初回停止済み (`SO:689–700`) なので、observer まで5回 retry するわけではない。 |
| 実測1 | **食い違いなし。** | 保存済み別 request でも両 racct が rc=1、同一 sudo marker。889948 と引数なしの当日値は brief を一次記録として読み、再実行はしていない。 |
| 実測2 | **なし。** | `パスワードが必要` は `ACCOUNTING_PERMISSION_MARKERS` に実在 (`RP:151–160`)、分類は最優先で `permission` (`RP:1634–1646`)。 |
| 実測3 | **field 存在は一致。ただし validator の記述は不完全。** | 実 `.e` に四 field はある。一方 `_accounting_valid.valid` はそれに加え exact count と `stream_provenance_valid` を要求する (`RP:1681–1730`)。signal preamble が Request ID より前にある `.e` は同 validator へ単純流用できない。 |
| 実測4 | **なし。** | 2-job artifact は request block 1個と空 stderr 1個で、`Number of Jobs: 2` の一行だけ ([manifest:23–39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent/output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260803T150807Z-5809d1d8d4d2f8c5/attempts/t361-flock/20260803T150808Z-t361-flock-a1-9060899fb1686d87/work/controller/job-output-manifest.json:23))。 |
| 実測5 | **実質一致、行 anchor にずれ。** | budget parser/delta は `RP:3098–3156`、initial gate の減少計算は `RP:5545–5558`。brief の `5543–5556` は2行早い。`point_conversion` は確かに `UNDETERMINED`。 |
| 実測6 | **一部不一致。** | 通常 run の rename 後は manifest/hash/size 照合される。しかし未改名 `*.e` は manifest なしで parser 候補となり、resolve path 3 に採用されうる。従って「`.e` は manifest 束縛付き」は全経路には成り立たない。また `_saved_nqsv_stderr_accounting` の return は `RP:2069` まであり、brief の `1882–2010` は関数途中で切れている。 |
| 実測7 | **内容は一致、行番号が1行ずれ。** | `REQUIRED_EXTERNAL_COMMANDS` は `RP:184–193`。`_command_paths` は `which`、存在、実行 bit しか見ない (`RP:785–795`)。brief の `183–192` は旧 anchor。 |
| 実測8 | **明確な誤り。** | subprocess 10本は正しいが sleep は **8秒ではなく16秒**。各 command で失敗後 sleep が4回、command は2本 (`RP:1769–1786`)。 |
| 成果物影響: CC synthesis へ流れない | **食い違いなし。** | repo 内の実装 consumer はこの probe controller/observer と証拠 artifact に閉じており、session summary も attempt 台帳の縮約だけ (`RP:5749–5769`)。 |
| 成果物影響: 「会計側からの独立裏取りが恒久的にゼロ」 | **過剰一般化。** | racct DB の独立裏取りがゼロ、なら正しい。しかし `.e` accounting block はすでに `termination_cause_consistent=true` と terminal path 3 を供給する。実例でも formal accounting は false のまま cause は true (`RESULT.md:13–20`)。 |
| 成果物影響: 現状放置時の既存 authority | **なし。** | 現コードを変えなければ authority 式は D161 どおり不変 (`RP:329–342`)。 |

### 6. 残る未解決点

1. **正式源の扱い**
   - 択 (a): racct を正式源のまま残し、permission 即時打切りにする（推奨）。
   - 択 (b): `.e` を非 gate の request-summary sidecar として正式化する。
   - 択 (c): `.e + qstat + qwait` composite を新 evaluation model で正式源にする。
   - 択 (d): 管理者所有の scheduler export receipt を新設する。

2. **permission retry**
   - 択 (a): record 不在かつ permission marker を得た command は1回で停止し、`empty/error` だけ retry する（推奨）。
   - 択 (b): 現行どおり permission も5回繰り返す。

3. **未改名 `.e` の resolve provenance**
   - 択 (a): qsub template・exact filename・expected file count を必須化し、現在の広い glob 受理を狭める（推奨）。
   - 択 (b): crash 回収可能性を優先して現状を維持する。
   - 択 (c): manifest-bound file だけを認め、rename 前 crash の path 3 を捨てる。

4. **外部 accounting 権威**
   - 択 (a): hazard probe には不要として管理側 collector を要求しない（推奨）。
   - 択 (b): 独立会計が必須として Pegasus 管理側との collector/spool 設計へ進む。

## 総括

- 推奨は、`.e` を既存の正式会計 fields へ昇格せず、racct permission を各 command 1回で打ち切る案 A。
- `accounting_available` 等と authoritative 式は変わらず、受理集合への影響はない。
- `.e` は request 単位・job-writable の mixed stream として、qwait/qstat と組み合わせた cause/terminal 証拠に限定する。
- ユーザー裁定は正式源、permission retry、未改名 `.e` の provenance、管理側 collector の4点。