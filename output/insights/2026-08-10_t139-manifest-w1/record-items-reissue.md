# [T-139] 段 A 記録項目 — 受領証 schema の要件文書 (再発行版)

```text
authority: none
default_effect: no-state-change
document_kind: receipt_schema_proposal
approval_status: draft_unapproved
supersedes: output/insights/2026-08-08_t139-addendum-a/record-items.md
supersedes_sha256: 1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3
```

> **承認状態について。** 本書は前版の**後継案**であって、それ自体はまだ承認されていない。
> 前版は D262 が承認済み blob として digest 固定している。**`F_e` (D262 を fold した commit) より
> 後に生まれた本書を `F_e` が承認することはできない。**本書が承認されるには、本書の digest を
> 名指しする新しい canonical 裁定と、それを台帳へ fold する commit `F_r` が要る。
> 承認 manifest は `F_r` の子孫にしか置けない。この構造は本 wave の裁定パッケージで
> ユーザーへ返してある (Q-D の「同一 land」と両立しない)。

## 0. 前版から変えた点 (この 3 つだけ)

1. **§2 (d) の `post_performance_failure` に第三の充足経路を足した** (ユーザー裁定 §58 Q-A)。
2. **前版 §3.1 が「未定義」と認めた nested object に exact key を与えた** (新 §4)。
   これが閉じない限り「完全な機械可読 schema」は書けない、という段 3 の指摘に対応する。
3. **第三分岐が開ける捏造余地を「本案が保証しないこと」へ明記した** (新 §6)。

**前版の §0 設計原則、§1 top-level 18 key、§2 (a)〜(c) (e)〜(g)、§3 の追補 A 対応表は、
本書でも逐語で有効である。**本書はそれらを緩めない。

---

## 1. top-level の exact key (18。前版から不変)

```text
schema_version  study_id  declared_use_class  study_stage
series_id  parent_series_id
preregistration  environment  measurement_checkout  dependency_pins
arms  allocations  planned_execution  actual_runs
correctness_evidence  liveness  admission_telemetry  attempts
```

`additionalProperties: false` を top-level と**全 nested object**へ課す。
**19 個目の top-level key を足すことは余剰 field 違反である。**追加はすべて既存 key の内側へ置く。

## 2. 設計原則 (D162 の直接適用。前版から不変)

- producer が書けるのは **raw な実行事実と証拠 pointer**、および**利用意図を示す閉集合の種別**だけ。
- 適格性状態・pairing の成否・受理状態・validator の identity / 結果は **未知 field として拒否**する。
- **本 schema のどの field も、単独では適格性の入力にならない。**消費側は producer の申告値を読まず、
  信頼された validator を同一呼出しの中で再実行する (D162 決定 (4))。
- 検査は単一 fd / snapshot で読み、hash と parse を同一 byte buffer に対して行う (D162 決定 (5))。
  symlink は拒否する。

---

## 3. `reason_code` の条件分岐 — **第三分岐を追加した (Q-A)**

`reason_code` の enum は前版から不変である。

```text
pre_performance_infra_failure | post_performance_failure | correctness_anomaly | completed
```

条件分岐は次のとおり。**変更したのは `post_performance_failure` の行だけである。**

| `reason_code` | 要求する条件 |
|---|---|
| `completed` | `allocation_id` と `performance_started_marker` の実在を要求し、36 run の完全双射を要求する |
| `pre_performance_infra_failure` | `performance_started_marker` が**不在**であることを要求する |
| `correctness_anomaly` | `replaces_attempt_id` を持てない (終端 reject であり置換されない) |
| `post_performance_failure` | **次の 3 経路のいずれか 1 つ以上**を満たす (下記) |

### 3.1 `post_performance_failure` の 3 経路

```text
経路 1: performance_started_marker が実在する                          (前版から不変)
経路 2: 性能 run の raw 痕跡が実在する                                  (前版から不変)
経路 3: a03 failure evidence と、それに対応する environment_observations[] 要素が
        ともに実在し、validator が raw から失敗を再計算できる           (本書で追加)
```

**なぜ第三経路が要るか。** 追補 A の `a04` は「`a03` 不成立は位置を問わず
`post_performance_failure` へ写す」を既定とする。ところが `a03` の観測窓は
**preflight phase の `[150, 160)` にも 1 つ置かれ**、その窓で不成立になった attempt は
marker (作成は `[165, 170)`) にも性能 run の raw 痕跡にも到達しない。
前版の 2 経路だけでは、**この正当な失敗を記録する経路が存在しなかった。**
記録できなければ「全 attempt を保存する」(core §7) が破れるか、marker の捏造を促す。

### 3.2 経路 3 の充足条件 (恒真化を避けるための拘束)

経路 3 は次を**すべて**満たすときにだけ成立する。producer の申告文字列は 1 つも入力にしない。

1. `attempts[].environment_observations[]` に、当該 attempt に属する要素が
   **少なくとも 1 つ**存在する。
2. その要素が `stat_before_raw` と `stat_after_raw` の**両方**を持ち、
   いずれも `{path, size, sha256}` の三つ組で実在し、bytes が読める。
3. **validator が raw から失敗を再計算できる。** すなわち、追補 A `a03` の
   fail-closed 事象表 (8 列未満 / 差分が負 / `total ≤ 0` / 窓長が `10.000 ± 0.100` 秒の外) の
   いずれか、または `cpu_busy_core_equivalents` が `[0.0, 1.0]` の外、
   **のどれか 1 つが raw から導けること。**
4. `monotonic_start_ns` と `monotonic_end_ns` が存在し、単調で、窓長を再計算できる。
5. `malformed_reason_or_null` が非 null の場合、その値は**再計算した事象と一致**しなければならない。
   一致しない受領証は拒否する。
   **位置づけを正確に書く** — 失敗の成立は raw のみから導出する。非 null の申告値は
   **負方向の整合性検査にだけ使う** (食い違えば拒否する) のであって、失敗成立の正の証拠にはしない。
   `null` の申告は経路 3 の成立を妨げない (raw から導ければよい)。
   したがってこの field は受理集合を**狭める方向にだけ**効く。
   「受理条件の入力にしない」という前版の言い方はこの点で不正確だったので改める。
6. `scope == preflight` の要素で経路 3 を満たす attempt は、
   `performance_started_marker` が `null` であり、かつ `actual_runs[]` に
   当該 attempt を参照する要素が**存在しない**ことを要求する。
   (preflight で落ちた attempt が性能 run を持つのは矛盾である。)

**`recovered` に相当する boolean field を持たせない**という前版の禁止は本書でも有効である。
経路 3 は「producer が失敗したと言った」ではなく「raw から失敗が導ける」で成立する。

### 3.3 受理集合はどちらへ動くか — **拡大である**

`R_old` を前版の受理集合、`R_new` を本書の受理集合とすると

```text
R_new = R_old ∪ { 経路 3 だけで post_performance_failure を満たす受領証 }
```

であり、**厳密な拡大**である。前版で拒否されていた markerless な attempt が受理候補に入る。
**この事実を安全性の根拠に使ってはならない。**承認は「拡大を承認する」ものとして扱う。
拡大に伴って新たに開く偽造余地は §6 に明記する。

---

## 4. 前版が未定義のまま残した nested object の閉包 (新規)

前版 §3.1 は、`allocations[]`・`liveness[]`・`admission_telemetry[]`・`attempts[]`・
`phase_caps[]`・`translation_units{}`・`cluster_slots[]` が
「要求される内容を書いてあるだけで key 単位の閉包を与えていない」と認めていた。
本節がその閉包を与える。**すべて `additionalProperties: false` を課す。**

### 4.1 `attempts[]`

```text
attempt_id  reason_code  replaces_attempt_id  parent_attempt_id
allocation_id  submitted_at_monotonic_ns  intent_ref
performance_started_marker  environment_observations[]  failure_evidence
```

- `attempt_id` は受領証内で一意。`replaces_attempt_id` は `attempts[]` 内の別 `attempt_id` か `null`。
  `reason_code == correctness_anomaly` のとき `replaces_attempt_id` は `null` でなければならない。
- `allocation_id` は `allocations[]` の `allocation_id` か `null`
  (qsub 失敗時は `null` にできるが **row 自体を省略できない**)。
- `intent_ref` は `{path, size, sha256}`。qsub より前に書いた durable submission intent を指す。
- `performance_started_marker` は `{path, size, sha256, created_at_monotonic_ns}` か `null`。
- `failure_evidence` は `{kind, pointer{path, size, sha256}}` か `null`。
  `kind ∈ {a03_environment, scheduler, driver, collector, correctness}`。

### 4.2 `attempts[].environment_observations[]`

```text
ordinal  scope  run_id_or_null
stat_before_raw{path,size,sha256}  stat_after_raw{path,size,sha256}
stat_before[]  stat_after[]
monotonic_start_ns  monotonic_end_ns
load1_diagnostic  malformed_reason_or_null
```

- `ordinal` は attempt 内で 1 起点の連番、欠番不可。
- `scope ∈ {preflight, pre_run}`。`scope == preflight` の要素は `run_id_or_null == null`。
  `scope == pre_run` の要素は `run_id_or_null` が `actual_runs[].run_id` を指す。
- `stat_before[]` / `stat_after[]` は `/proc/stat` の `cpu` 集計行の**8 列**
  (`user, nice, system, idle, iowait, irq, softirq, steal`) を整数で持つ。
  **8 列に満たない raw も可変長 pointer (`*_raw`) として保存する。zero-fill しない。**
  8 列に満たないときは `stat_before[]` / `stat_after[]` を実列数のまま置き、
  `malformed_reason_or_null` に `short_columns` を置く。
- `load1_diagnostic` は診断値であり**受理条件の入力にしない**。
- `malformed_reason_or_null ∈ {null, short_columns, negative_delta, nonpositive_total, window_out_of_range}`。

### 4.3 `allocations[]`

```text
allocation_id  allocation_role  path_choice  path_choice_intent{path,size,sha256}
node  requested_walltime_s  internal_deadline_s
started_at_monotonic_ns  ended_at_monotonic_ns
accounting_trace{path,size,sha256}  exclusivity{method, raw{path,size,sha256}}
phase_caps[]  phase_events[]  binary_rehash[]
```

- `allocation_role ∈ {performance_cluster, verification}`。
- `path_choice ∈ {primary_build_outside, fallback_build_inside}` で、
  **投入前に固定した値であることを示す durable intent pointer (`path_choice_intent`) を伴う。**
- `exclusivity` は単独性検査の**生出力 pointer** を持ち、boolean を持たない。
- `phase_caps[]` の各要素は `{phase, cap_s, sub_cap_s_or_null}`、
  `phase ∈ {preflight, observation, decision, marker, run, teardown}`。
- `phase_events[]` の各要素は `{phase, event, monotonic_ns}`、
  `event ∈ {enter, leave, term_signal}`。
- `binary_rehash[]` は 3 要素固定 (`{point, arm, sha256, monotonic_ns}`、
  `point ∈ {after_staging, before_first_run, after_last_run}`)。

### 4.4 `liveness[]`

```text
ordinal  probe  monotonic_ns  raw{path,size,sha256}
```

`probe` は閉集合 `{allocation_alive, driver_heartbeat, filesystem_writable}`。
**verdict 文字列や boolean を置ける型を持たない** (再実行可能な pointer だけ)。

### 4.5 `admission_telemetry[]`

```text
ordinal  kind  receipt{path,size,sha256}  fixed_inputs{B, seed, input_sha256}
ledger_evidence
```

- `kind ∈ {j_derivation, q_derivation, calibration_simulation, alpha_reservation}`。
- **producer の `pass` 申告を権威にしない。** `receipt` は transcript の raw pointer であり、
  validator が再計算する。
- `kind == alpha_reservation` の要素だけが `ledger_evidence` を持つ
  (`{ledger_path, family_root, ordinal, reservation_entry_sha256, reservation_commit}`)。
  **受領証の `ordinal` は自己申告であり権威ではない。** validator は台帳を読み直し
  `(family_root, ordinal)` の重複が無いことを確認する。
- **追補 B `b03` の個別公表系列台帳は、本 schema の必須記録項目にしない。**
  `b03` 自身が「core §12 の必須記録項目を増やさず、validator の受理条件を追加しない」と課しており、
  公表台帳の予約は投入前 admission 側の検査に属する。ここへ入れると core の変更になる。

### 4.6 `planned_execution.cluster_slots[]`

```text
cluster_slot  workload  block_index  permutation
```

`permutation` は `{SDX, SXD, DSX, DXS, XSD, XDS}` の enum。
**置換 attempt は `cluster_slot` を新設せず、置換対象と同じ slot を参照する。**

### 4.7 `arms.*.compile.translation_units{}`

**本 object は §1 の「全 nested object へ `additionalProperties: false`」の唯一の明示例外であり、
map 型として扱う。**例外にする以上、閉包は 2 方向から与える。

- **値の閉包** — `additionalProperties` は `{normalized_argv[], sha256}` の exact object 型に固定する
  (値側に自由 key を許さない)。
- **key の閉包** — key は TU の **repo 相対 path** であり、`propertyNames` で機械的に拘束する。
  散文の「repo 相対 path」だけでは、絶対 path・`..`・空 key・非正規化 alias の受理が実装依存になる。

```text
propertyNames: 先頭が "/" でない / "./" と "../" の segment を含まない /
               空文字列でない / 連続する "/" を含まない / 末尾が "/" でない /
               NUL・CR・LF を含まない
正規化規則:    受領証へ書く前に POSIX 正規化を済ませた形だけを許す。
               validator は正規化を再適用し、key と一致しなければ拒否する
               (validator 側で正規化して受け入れ直す = 別表記の同一 TU を作れる、を禁じる)
```

**全 TU を持つ (3 TU に限定しない)。** key の数に上限を置かない。

---

## 5. 前版から不変の要求 (再掲。緩めない)

- `planned_execution.runs[]` は 1 cluster **36 要素** (6 permutation block × 3 arm × 2 workload)。
- `completed` の attempt だけが planned ↔ actual の**完全双射**を要求される。
  失敗 attempt は planned schedule に対する**厳密な prefix** であり、failure evidence pointer を伴う。
  **欠けた run を後から補って双射を成立させることを禁じる。**
- 絶対規律 1 — `arms.*.compile` は `trace_enabled: false` / `analysis_enabled: false` を必須とし、
  `correctness_evidence[].build` は `trace_enabled: true` / `analysis_enabled: true` を持つ。
  **`correctness_evidence[].build.binary.sha256` は同じ arm の `arms.*.binary.sha256` と
  一致してはならない。**
- **否定検査を必須にする** — 消費側が `declared_use_class`、`admission_telemetry[].returncode`、
  `attempts[].reason_code == "completed"`、`allocations[].exclusivity` のいずれかを
  受理条件の入力に使ったら落ちるテストを置く。
- 受領証を永続化する関数自体が `PreregBinding` を必須 keyword-only で受ける。

---

## 6. 本案が保証しないこと (第三分岐で 1 項増えた)

- **★ 経路 3 は、不利な実 run を「実行しなかった」に見せかける経路を開く (新規)。**
  producer は preflight 観測窓で意図的に malformed な raw
  (7 列の `cpu` 行、負差分、窓長逸脱) を書けば、marker も性能 run も持たない attempt を
  正当な `post_performance_failure` として記録できる。
  §3.2 の 6 条件は「raw から失敗が導けること」までしか強制できず、
  **その raw が実際のカーネル出力かどうかは producer 権限内では判別できない。**
  certified 値を直接上げることはできない (固定 `J` の完全性 gate が別に効く) が、
  **試行台帳における「この試行は実行されなかった」という事実そのものが偽造可能になる。**
  閉じるには producer 権限外の collector が raw を独立に採取する必要があり、
  それは本書の射程外である。**この残余は承認時に明示的に引き受けられたものとして扱う。**
- **台帳の外で走らせた投入は見えない。**
- **producer が実際とは異なる bytes や schedule で走らせながら整合した受領証を作る偽造は
  検出できない。**受領証の三つ組と `measurement_head` の照合が検出するのは
  「producer が書いた 2 つの文書の食い違い」であり、実測 checkout の一致ではない。
- **`a03` の恒真化は静的検査では防げない。**本 schema は raw counter の保存を強制することで
  再計算を**可能にする**が、実装が実際に再計算することは保証しない。
- **本書は実装ではない。** schema を機械化する producer / validator は未実装である。
- **本書は承認されていない。** §0 の承認状態を参照。
