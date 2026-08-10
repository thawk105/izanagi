# [T-139] 段 A 記録項目 — 受領証の要件文書 (v2。自己完結版)

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / main_study / record_items
document_kind: receipt_schema_requirements
supersedes: output/insights/2026-08-08_t139-addendum-a/record-items.md
supersedes_sha256: 1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3
supersedes_draft: output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md
supersedes_draft_sha256: 5f07e9177736739fdb80a7df00a84c6f84751bf8d3c5e686adc447873a273d54
```

## 0. 本書の位置づけ

本書は、凍結事前登録 core §12 が要求する記録項目を、**受領証 1 枚の exact key 集合として閉じる要件
文書**である。対応する機械可読 schema は同ディレクトリの `receipt-schema-v1.json` であり、
本書と schema の関係は §7 が定める。

- **本書は自己完結である。** 受理条件を他 blob への参照で取り込まない。前 2 版
  (`record-items.md` / `record-items-reissue.md`) の受理条件は、緩めずに本書へ再掲した。
  前 2 版は本書の**規範的依存ではない** — resolver は本書だけを読む。
- **承認状態は本書に書かない。** どの blob が承認済みかを定めるのは canonical 台帳とその
  approval manifest だけである (`authority: none` は「本書が可変状態の正本ではない」を意味する)。
- **本書が新設した閉包 (承認済み文書から一意には導けない選択) は §10 に全件を列挙する。**
  承認は、この閉包を含めて承認するという意味になる。
- 本書は実装ではない。schema を機械化する producer / validator の実装は本書の射程外である。

### 0.1 受領証の粒度と terminal 性 (前 2 版が定めていなかった)

**受領証 1 枚は study stage 1 つ**に対応する (`study_stage ∈ {pilot, main_run}`)。
1 割当てに 1 枚ではない。理由は次の 3 つで、いずれも前 2 版の本文から導かれる。

1. `attempts[]` は置換関係 (`replaces_attempt_id`) を持つ。置換は**別の割当て**で行われるため、
   1 割当ての受領証では置換関係が受領証を跨ぎ、参照整合性を検査できない。
2. `a13` の予約 (`(family_root, ordinal)`) と `series_id` は study に 1 つであり、割当てごとに増えない。
3. 追補 A `a01` (B) の検証割当ては **study 全体で 1 本**であり、その correctness / liveness 証拠を
   性能割当ての受領証へ 1 枚ずつ複製すると、同じ証拠が複数の受領証で別々に申告されうる。

したがって「1 cluster = 36 run」は**割当てあたりの件数**であり、配列長の上限ではない。
pilot の受領証は `36 × |consumed_cluster_slots|` の planned run を持つ。

**受領証は stage の terminal receipt である。** 全 attempt が terminal な `reason_code` を持ち、
実行中・投入待ちの中間状態を受領証に載せない (中間状態は durable submission intent と
attempt 台帳側に残る)。したがって「まだ走っている attempt」を表す `reason_code` は存在しない。

**`cluster_slot` の番号空間は stage-local である。** `pilot` の slot `j` と `main_run` の slot `j` は
別の割当てを指す。受領証内の全参照は自 stage に閉じ、他 stage の run / attempt / allocation を
参照してはならない。

**検証割当ては study 全体で 1 本である。** `pilot` と `main_run` の受領証は、**同一の
`allocation_id` と同一 bytes** でその 1 本を記録する (2 本目を作らない)。同一性は
`allocation_id` と `accounting_trace` / `exclusivity.raw` の digest 一致で検査する。

### 0.2 前 2 版から変えた点 (すべて受理条件に効く)

| # | 変更 | 理由 |
|---|---|---|
| C1 | `post_performance_failure` に第三の充足経路 (`a03` 不成立証拠) を足した | 追補 A `a04` は `a03` 不成立を位置を問わず開始後の失敗へ写すが、preflight 窓で落ちた attempt は marker も性能 raw も持てず、前版には記録経路が無かった (core §7 の全 attempt 保存が破れる) |
| C2 | `pre_performance_infra_failure` の条件を `a04` 準拠へ**狭めた** | 前版と草案は marker 不在だけを条件にしており、性能 raw を持つ attempt を予備置換可能にしていた (`a04` が禁じる) |
| C3 | 全 nested object の exact key・型・必須性・配列長を閉じた | 前版 §3.1 が未閉包を自認していた。閉じないと同じ受領証が実装 A で適格・B で拒否になる |
| C4 | `binary_rehash[]` を **到達 point 条件つきの最大 9 要素** (3 arm × 3 点) にした | `a05` は 3 arm の各 executable を 3 点で再 hash する。前版の「3 要素固定」では 2 arm 分が欠落する。一方、preflight で落ちた割当てには `before_first_run` / `after_last_run` が存在しない |
| C5 | `malformed_reason` を malformed 時に**非 null 必須**にし、**評価順序**を固定した | 前版と草案は null 可否が節間で矛盾し、複数事象が同時成立したときの値も定まらなかった |
| C6 | `exclusivity.method` の enum を閉じ、boolean を持たせないことを明記した | 前版は key だけで enum が開いていた (§10 の閉包 2) |
| C7 | `a13` の検査を **append-only 全履歴**にした | 前版は現 tip の重複検査だけで、過去行を削除して同じ `(family_root, ordinal)` を再利用した履歴を受理した |
| C8 | 消費する cluster slot を受領証 field として固定し、pilot では **1〜8** とした | `a09` は slot 1〜13 の schedule を発行するが、pilot がどの 8 本かを定めておらず、結果を見て選べた (§10 の閉包 1) |
| C9 | schedule 表の **canonical bytes** を逐語で定義した | `schedule_sha256` の対象 bytes が未定義で、validator がゼロから再導出して照合できなかった (§10 の閉包 4) |
| C10 | `admission_telemetry[].kind` の `calibration_simulation` を `stress_check_simulation` へ改めた | core §7 の較正義務は erratum によって「事前固定 stress model のもとでの確認」へ置換される。**この改名は erratum の承認に従属する** |
| C11 | 否定検査の列挙を**実在 field だけ**にし、qsub の returncode を `attempts[].qsub_result.returncode` として実在させた | 前版は存在しない `admission_telemetry[].returncode` を挙げており、否定検査が空振りしていた |
| C12 | 第三分岐が開ける捏造余地を非保証として明記した | 承認時に引き受ける残余であることを文書に固定する (§9) |
| C13 | **受領証の粒度を study stage 1 つに定め、terminal 性と stage-local slot を明記した** (§0.1) | 前 2 版は粒度を定めておらず、1 割当て 1 枚と読むと置換関係が受領証を跨いで検査不能になり、検証割当ての証拠が複数受領証に重複申告される |
| C14 | `liveness[].probe` に `liveness_run` を足した | 追補 A `a01` (B) が要求する 2 workload × 3 arm の liveness run を、前版の 3 値 enum では記録できなかった |
| C15 | **割当ての phase enum を役割別にした** | 追補 A `a01` は (A) 性能割当てと (B) 検証割当てで phase 構成が異なる。単一 enum では検証割当てが架空の marker / run phase を書かされる |

## 1. 設計原則 (D162 の直接適用)

- producer が書けるのは **raw な実行事実と証拠 pointer**、および**利用意図を示す閉集合の種別**だけである。
- 適格性状態・pairing の成否・受理状態・validator の identity / 結果は **未知 field として拒否**する。
- **本 schema のどの field も、単独では適格性の入力にならない。** 消費側は producer の申告値を読まず、
  信頼された validator を同一呼出しの中で再実行する (D162 決定 (4))。
- 検査は単一 fd / snapshot で読み、hash と parse を同一 byte buffer に対して行う (D162 決定 (5))。
  symlink は拒否する。path の各 component を `O_NOFOLLOW` で辿り、`fstat` / hash / parse を
  同一 fd に対して行う。
- producer が申告した派生値 (再計算可能な値) は、**受理集合を狭める方向にだけ**使う。
  validator は必ず raw から再計算し、申告値との不一致を拒否理由にする。一致は受理の正の根拠にしない。

## 2. top-level の exact key (18。前版から不変)

```text
schema_version  study_id  declared_use_class  study_stage
series_id  parent_series_id
preregistration  environment  measurement_checkout  dependency_pins
arms  allocations  planned_execution  actual_runs
correctness_evidence  liveness  admission_telemetry  attempts
```

`additionalProperties: false` を top-level と**全 nested object**へ課す。
**19 個目の top-level key を足すことは余剰 field 違反である。**追加はすべて既存 key の内側へ置く。

### 2.1 事前登録 §12 との対応

| §12 の必須項目 | key |
|---|---|
| core / 追補 A / 追補 B の三つ組、限定例外を発効させた fold commit | `preregistration.{core,addendum_a,addendum_b,fold_commit}` |
| 環境タグ・環境証明 | `environment.{env_tag,attestation_mode,attestations}` |
| 測定 checkout (repo / CCBench の head) | `measurement_checkout.{repository_head,ccbench_head}` |
| 依存の pin | `dependency_pins[]` |
| build identity・compile argv・割当て外 build の binary hash | `arms.*.{compile,binary,built_outside_allocation}` |
| 割当て ID・node・時刻・会計痕跡・単独性検査 | `allocations[]` |
| 3 arm の source / binary / compile identity | `arms.{stock,mode1,modeX}` |
| 計画した実行順序と実際の実行順序、位置・直前 arm・timestamp・raw TPS | `planned_execution.runs[]`, `actual_runs[]` |
| correctness の証拠 (再実行できる形) | `correctness_evidence[]` |
| liveness、admission telemetry | `liveness[]`, `admission_telemetry[]` |
| 全 attempt、理由コード、置換関係、親系列 ID | `attempts[]`, `parent_series_id` |
| 利用意図の種別 | `declared_use_class` |

## 3. 共通型 (schema の `definitions`)

```text
fileRecord = { path, size, sha256 }
    path   : repo 相対。先頭 "/" 不可、".." segment 不可、空・末尾 "/" 不可、NUL/CR/LF 不可
    size   : 0 以上の整数
    sha256 : ^[0-9a-f]{64}$

blobRef    = { path, commit, sha256 }
    commit : ^[0-9a-f]{40}$

hex40 = ^[0-9a-f]{40}$      hex64 = ^[0-9a-f]{64}$
monotonic_ns = 0 以上の整数 (同一割当て内で単調)
```

## 4. top-level 各 key の exact 閉包

### 4.1 scalar 4 key + 系列 2 key

```text
schema_version    const "t139-receipt/v1"
study_id          ^[a-z0-9][a-z0-9-]{0,63}$
declared_use_class enum { official, exploration, qualification, dry }
study_stage       enum { pilot, main_run }
series_id         hex64
parent_series_id  hex64 | null
```

`declared_use_class` は**利用意図**であり、`qualification` は「適格性審査へ提出する」の意味で
**合格宣言ではない**。

### 4.2 `preregistration` (exact 8)

```text
core                  blobRef
addendum_a            blobRef
addendum_b            blobRef | null
fold_commit           hex40          限定例外 (D234) を canonical 台帳へ fold した commit
errata[]              { erratum_id, path, commit, sha256, approval_fold_commit }
approval_manifest     blobRef
receipt_schema        blobRef        本受領証が適合を主張する schema blob
composed_core_sha256  hex64          errata 適用後の実効 core digest (申告値。validator が再計算)
```

- `erratum_id` は `^[a-z0-9][a-z0-9-]{0,63}$`。`errata[]` は 1 要素以上、`erratum_id` は互いに異なる。
- **権威は approval manifest 側**である。`errata[]`・`receipt_schema`・`composed_core_sha256` は
  照合対象であって trust root ではない。
- **approval manifest は受領証 schema blob の digest を pin しなければならない。**
  validator は `receipt_schema.sha256` が manifest の pin と一致することを要求し、
  受領証の自己申告を信用しない。schema は pilot 投入より前に発行され、その digest が
  `PreregBinding` に固定される。
- **approval manifest は各 erratum blob の digest も pin しなければならない。**
  erratum 文書の固有検査は「宣言した `new_sha256` / `expected_composed_sha256` と自分の
  `new_text` が整合するか」までしか見られないため、**それらを一緒に差し替えた自己整合な偽 erratum は
  固有検査だけでは拒否できない。**唯一の anchor は台帳が承認した blob digest であり、
  resolver は `errata[].sha256` を manifest の pin と、さらに manifest を `F_r` の台帳 payload と
  exact 一致させたうえで適用しなければならない。

### 4.3 `environment` (exact 3)

```text
env_tag            ^[a-z0-9][a-z0-9._-]{0,63}$
attestation_mode   const "required"
attestations[]     { ordinal, profile_kind, schema_version, raw }
    ordinal        1 起点連番、欠番不可
    profile_kind   enum { expected, observed }
    schema_version 生 artifact 自身が持つ版文字列
    raw            fileRecord (正規化前の生 bytes)
```

`attestation_mode` に `none` を許さない。環境証明の無い受領証は §12 の必須項目を満たせない。
`profile_kind == expected` は**ちょうど 1 件**、`observed` は **1 件以上**とする。

### 4.4 `measurement_checkout` (exact 2)

```text
repository_head  hex40
ccbench_head     hex40
```

### 4.5 `dependency_pins[]` (exact 2 key、要素数ちょうど 5)

```text
{ name, commit }
    name    enum { gflags, glog, masstree, mimalloc, googletest }
    commit  hex40
```

`name` は 5 件すべてが exact 1 回現れる。値は追補 A `a08` の依存 pin と一致しなければならない。

### 4.6 `arms` (exact 3 key: `stock` / `mode1` / `modeX`)

各 arm は exact 4 key。

```text
compile                    object (下記)
binary                     fileRecord      性能 executable
built_outside_allocation   { artifact_path, size, sha256 }   検証割当ての immutable artifact
toolchain                  object (下記)
```

**`built_outside_allocation` は予備経路でも必須である。** 追補 A `a06` は「予備経路では性能 cluster
割当ての中で build するが、得られた binary の SHA-256 が**検証割当ての artifact と一致しなければ
fail-closed で reject する**」と課しており、検証割当ての artifact は予備経路でも実在する。

`compile` は exact 9 key。

```text
source            { repo_commit(hex40), ccbench_pin(hex40), base_tree_sha(hex40),
                    patch_path(string|null), patch_sha256(hex64|null) }
mode_macro        string | null      stock は null、mode1/modeX は追補 A a08 の逐語
configure_argv[]  string[]           要素と順序を exact 比較する
translation_units object             key = repo 相対 TU path、値 = { normalized_argv[], sha256 }
identity_sha256   hex64
trace_enabled     const false
analysis_enabled  const false
cmake_cache       { trace(integer enum [0]), add_analysis(integer enum [0]) }
compile_commands  fileRecord         build 時の compile_commands.json 実体
```

- `base_tree_sha` は `repo_commit` の tree object id であり、validator が再導出して照合する。
- `patch_path` / `patch_sha256` は `stock` で null、`mode1` / `modeX` で非 null。
- `translation_units` は **`patternProperties` + `additionalProperties: false`** で閉じる
  (`additionalProperties` に schema を与える形は使わない)。key の文法は §3 の `path` と同じで、
  受領証へ書く前に POSIX 正規化を済ませた形だけを許す。validator は正規化を再適用し、
  key と一致しなければ拒否する。**全 TU を持つ (件数に上限を置かない)。**
- **申告値と実体の照合を必須にする** (§6.3)。`trace_enabled` / `analysis_enabled` / `cmake_cache` は
  producer の boolean 申告に過ぎないので、validator は `configure_argv` 中の macro 定義、
  `compile_commands` 実体、`CMakeCache.txt` 由来の値を再読して 3 者一致を要求する。

`toolchain` は exact 6 key。

```text
compiler_path      string
compiler_version   string
compiler_sha256    hex64
link_argv[]        string[]
dynamic_deps[]     { soname, resolved_path, sha256 }
elf_interpreter    string
```

### 4.7 `allocations[]` (exact 16 key)

```text
allocation_id              ^[a-z0-9][a-z0-9._:-]{0,127}$   受領証内で一意
allocation_role            enum { performance_cluster, verification }
cluster_slot_or_null       integer 1..13 | null            performance_cluster は非 null、verification は null
scheduler_request_id       string
path_choice                enum { primary_build_outside, fallback_build_inside }
path_choice_intent         fileRecord   投入前に固定したことを示す durable intent
node                       string
requested_walltime_s       integer > 0
internal_deadline_s        integer > 0
started_at_monotonic_ns    monotonic_ns
ended_at_monotonic_ns      monotonic_ns
accounting_trace           fileRecord
exclusivity                { method, raw }
phase_caps[]               { phase, cap_s, sub_cap_s_or_null }
phase_events[]             { phase, event, monotonic_ns }
binary_rehash[]            { point, arm, sha256, monotonic_ns }
```

```text
exclusivity.method  enum { node_local_process_scan, scheduler_accounting }
exclusivity.raw     fileRecord   検査の生出力。boolean・verdict 文字列を置ける型を持たない
phase_events[].event enum { enter, leave, term_signal }
binary_rehash[].point enum { after_staging, before_first_run, after_last_run }
binary_rehash[].arm   enum { stock, mode1, modeX }
```

**phase の閉集合は `allocation_role` ごとに異なる** (追補 A `a01` (A) / (B) の phase 構成が異なる)。

```text
allocation_role == performance_cluster:
    phase enum { preflight, observation, decision, marker, run, teardown }
allocation_role == verification:
    phase enum { staging, build, build_post, correctness_run, evidence, teardown }
```

- `phase_caps[]` は当該 role の phase ごとに exact 1 件。`phase_events[]` の `phase` も同じ閉集合に従う。
- `requested_walltime_s` は `performance_cluster` かつ `path_choice == primary_build_outside` で 3600、
  `fallback_build_inside` で 5400、`verification` で 3600 とする (追補 A `a01` / `a06`)。
- **`binary_rehash[]` は到達した point の分だけを持つ** (要素数 0〜9、`(point, arm)` の重複禁止)。
  - `after_staging`: 性能 binary を staging した割当ては 3 arm 分を持つ。
  - `before_first_run`: 当該割当てで 1 run 以上を開始したときに 3 arm 分を持つ。
  - `after_last_run`: 当該割当てで 1 run 以上を完了したときに 3 arm 分を持つ。
  - `allocation_role == verification` の割当ては性能 run を持たないため **0 要素**とする
    (検証割当ての artifact identity は `arms.*.built_outside_allocation` が担う)。

### 4.8 `planned_execution` (exact 8)

```text
workloads               { W1, W2 }
schedule_seed           hex64        追補 A a09 の逐語 seed
schedule_algorithm      const "t139-a09-v1"
schedule_table          fileRecord   §6.6 の canonical bytes 実体
schedule_sha256         hex64        schedule_table の bytes の SHA-256 (申告値。validator が再導出)
consumed_cluster_slots[] integer[]   当該 stage が消費する slot 集合 (昇順・重複なし)。
                                     study_stage == pilot では **exact [1,2,3,4,5,6,7,8]**
cluster_slots[]         { cluster_slot, workload, block_index, permutation }  **156 要素**
runs[]                  下記 exact 10 key
```

```text
workloads.W1 / W2 = { driver_argv[], effective_flags, opt_parameters }
    effective_flags = { clocks_per_us(number), epoch_time(number), extime(number),
                        thread_num(integer), ycsb_max_ope(integer), ycsb_rmw(integer),
                        ycsb_rratio(integer), ycsb_tuple_num(integer), ycsb_zipf_skew(number) }
    opt_parameters  = { ADD_ANALYSIS, BACK_OFF, KEY_SIZE, MASSTREE_USE,
                        NO_WAIT_LOCKING_IN_VALIDATION, PARTITION_TABLE, PROCEDURE_SORT,
                        SLEEP_READ_PHASE, VAL_SIZE, WAL }   すべて integer

runs[] = { run_id, cluster_slot, workload, block_index, permutation,
           planned_ordinal, position, predecessor_arm, arm,
           preceding_wait { kind, required_s } }
    workload         enum { W1, W2 }
    block_index      integer 1..6       **workload-local** (追補 A a09 は workload ごとに 6 block)
    permutation      enum { SDX, SXD, DSX, DXS, XSD, XDS }
    position         integer 1..3        block 内の位置
    predecessor_arm  enum { START, stock, mode1, modeX }
    arm              enum { stock, mode1, modeX }
    preceding_wait.kind      enum { none, arm_gap, block_gap, workload_switch }
    preceding_wait.required_s integer enum [0, 30, 60]
```

- `runs[]` は `consumed_cluster_slots` の**各 slot についてちょうど 36 要素**
  (6 permutation block × 3 arm × 2 workload)。pilot なら合計 288 要素。
- **`position == 1` と `predecessor_arm == START` は同値**である (双方向の含意を課す)。
- `cluster_slots[]` は 13 slot × 12 block (2 workload × 6) = **156 要素**で、§6.6 の schedule 表と
  1 対 1 に対応する。
- `effective_flags` と `opt_parameters` の値は追補 A `a07` の表と exact 一致でなければならない。

### 4.9 `actual_runs[]` (exact 19 key)

```text
run_id                   planned_execution.runs[].run_id を指す
attempt_id               attempts[].attempt_id を指す
allocation_id            allocations[].allocation_id を指す
cluster_slot             integer 1..13
workload                 enum { W1, W2 }
block_index              integer 1..6
permutation              enum { SDX, SXD, DSX, DXS, XSD, XDS }
actual_ordinal           integer >= 1   当該 attempt 内の実行順 (1 起点、欠番不可)
position                 integer 1..3
predecessor_arm          enum { START, stock, mode1, modeX }
arm                      enum { stock, mode1, modeX }
preceding_wait           { kind, required_s, monotonic_start_ns, monotonic_end_ns }
started_at_monotonic_ns  monotonic_ns
ended_at_monotonic_ns    monotonic_ns
binary_sha256            hex64
exec_witness             { path, inode, size, sha256, monotonic_ns }
argv_sha256              hex64
argv_raw                 fileRecord   実 argv の canonical bytes
run_log                  fileRecord   raw TPS を含む run log 実体
```

`tps` の**数値は受領証に置かない** — raw TPS は `run_log` の bytes として保存し、validator が
そこから抽出する。producer が別途書いた数値は二重の真実を作る。
`preceding_wait` は producer が `satisfied` boolean を書かず、validator が秒数を再計算する。

### 4.10 `correctness_evidence[]` (exact 6 key)

```text
ordinal      1 起点連番、欠番不可
arm          enum { stock, mode1, modeX }
workload     enum { W1, W2 }
build        { source, compile, binary }
    source   arms.*.compile.source と同一形
    compile  { identity_sha256, argv[], trace_enabled(const true), analysis_enabled(const true),
               cmake_cache{ trace(integer enum [1]), add_analysis(integer enum [1]) },
               compile_commands(fileRecord) }
    binary   fileRecord
run_scope    { allocation_id, run_ordinal }
outputs[]    fileRecord[]   **1 要素以上**。再実行可能な pointer のみ。
                            verdict 文字列・boolean を置ける型を持たない
```

- **検証割当ての attempt が `completed` の受領証では要素数ちょうど 6** (2 workload × 3 arm)。
  `(arm, workload)` の組が過不足なく現れる。検証割当てが失敗した stage では、
  実際に得られた件数だけを持つ (0 件を含み、失敗は当該 attempt の `failure_evidence` が担う)。
- `run_scope.allocation_id` は `allocation_role == verification` の割当てを指し、
  **性能 run と同じ `allocation_id` / `run_id` を指してはならない** (絶対規律 1、追補 A `a01`)。
- `build.binary.sha256` は同じ arm の `arms.*.binary.sha256` と**一致してはならない**。
- `build.compile` の申告値も §6.3 の 3 者一致検査 (argv macro / `compile_commands` / `CMakeCache`) の
  対象である。

### 4.11 `liveness[]` (exact 7 key)

```text
ordinal            1 起点連番、欠番不可
allocation_id      allocations[].allocation_id を指す
probe              enum { liveness_run, allocation_alive, driver_heartbeat, filesystem_writable }
arm_or_null        enum { stock, mode1, modeX } | null
workload_or_null   enum { W1, W2 } | null
monotonic_ns       monotonic_ns
raw                fileRecord
```

- `probe == liveness_run` の要素は `arm_or_null` / `workload_or_null` がともに非 null。
  検証割当ての attempt が `completed` の受領証では**ちょうど 6 件**あり `(arm, workload)` を
  過不足なく覆う (追補 A `a01` (B))。検証割当てが失敗した stage では得られた件数だけを持つ。
- それ以外の `probe` は両方 null とする。
- **verdict 文字列や boolean を置ける型を持たない** (再実行可能な pointer だけ)。

### 4.12 `admission_telemetry[]` (exact 5 key)

```text
ordinal        1 起点連番、欠番不可
kind           enum { j_derivation, q_derivation, stress_check_simulation, alpha_reservation }
receipt        fileRecord   transcript の raw pointer
fixed_inputs   { input_sha256(hex64), B_or_null(integer|null), seed_or_null(hex64|null) }
ledger_evidence { ledger_path, family_root, ordinal, reservation_entry_sha256, reservation_commit } | null
```

- **性能割当てを 1 本以上投入した stage の受領証では、`kind == alpha_reservation` を
  ちょうど 1 件持たなければならない** (`a13` は pilot 投入より前に canonical 台帳の予約を要求する)。
- **`stress_check_simulation` を 1 件以上持たなければならない** (core §7 の事前 simulation は
  pilot 1 本目の投入より前に完走する。追補 A `a12`)。
- **`j_derivation` と `q_derivation` は、`J` を導出する stage (本走の投入前) で各 1 件以上**とする。
  pilot の受領証では 0 件でよい (`J` は pilot 母数から導かれるため pilot の後に確定する)。
- `kind == stress_check_simulation` のときだけ `B_or_null` と `seed_or_null` が非 null
  (Monte Carlo の反復数と seed)。`j_derivation` / `q_derivation` / `alpha_reservation` は
  閉形式または台帳読取であり、ともに null とする。
- `kind == alpha_reservation` のときだけ `ledger_evidence` が非 null。他は null。
- `ledger_evidence.family_root` は hex40、`reservation_commit` は hex40、
  `reservation_entry_sha256` は hex64、`ordinal` は 1 以上の整数。
- **producer の `pass` 申告を権威にしない。** validator は transcript を再計算する。
- **受領証の `ordinal` は自己申告であり権威ではない** (§6.7 の全履歴検査が権威)。
- 追補 B `b03` の個別公表系列台帳は本 schema の必須記録項目にしない。`b03` 自身が
  「core §12 の必須記録項目を増やさず、validator の受理条件を追加しない」と課しており、
  公表台帳の予約は投入前 admission 側の検査に属する。**追補 B は段階 1 (草案) に留め置かれており、
  公表台帳の記録要件は新 core 側で定まった時点で再評価を要する。**

### 4.13 `attempts[]` (exact 12 key)

```text
attempt_id                 受領証内で一意
cluster_slot_or_null       integer 1..13 | null    性能 attempt は非 null、検証 attempt は null
reason_code                enum { pre_performance_infra_failure, post_performance_failure,
                                  correctness_anomaly, completed }
replaces_attempt_id        attempts[] 内の別 attempt_id | null
parent_attempt_id          attempts[] 内の別 attempt_id | null
allocation_id              allocations[].allocation_id | null   (qsub 失敗時は null。**row は省略できない**)
submitted_at_monotonic_ns  monotonic_ns
intent_ref                 fileRecord   qsub より前に書いた durable submission intent
qsub_result                { returncode(integer), raw(fileRecord) }
performance_started_marker { path, size, sha256, created_at_monotonic_ns } | null
environment_observations[] 下記 exact 11 key
failure_evidence           { kind, pointer } | null
    kind    enum { a03_environment, scheduler, driver, collector, correctness }
    pointer fileRecord
```

- **`intent_ref` は create-only で書かれた durable submission intent を指す** — qsub より**前**に
  書き、以後上書きしない。validator は同一 path の内容が attempt 間で変化していないことを要求する。
- **`performance_started_marker` も create-only** である。既存 marker を上書きした痕跡
  (同一 path で異なる digest) を持つ受領証は拒否する。
- job 側 preflight の reject を回収する collector を同じ実装単位に含める
  (`qsub_result.raw` と `failure_evidence.pointer` がその回収物を指す)。
- `attempts[]` は durable intent の全 attempt を **exact に被覆**する (部分被覆を許さない)。

### 4.14 `attempts[].environment_observations[]` (exact 11 key)

```text
ordinal               1 起点連番、欠番不可
scope                 enum { preflight, pre_run }
run_id_or_null        actual_runs[].run_id | null
stat_before_raw       fileRecord
stat_after_raw        fileRecord
stat_before[]         integer[]   /proc/stat の cpu 集計行の列。**1〜8 要素。実列数のまま置く**
stat_after[]          integer[]
monotonic_start_ns    monotonic_ns
monotonic_end_ns      monotonic_ns
load1_diagnostic      number      診断値。**受理条件の入力にしない**
malformed_reason      enum { short_columns, negative_delta, nonpositive_total,
                             window_out_of_range } | null
```

- `scope == preflight` の要素は `run_id_or_null == null`。`scope == pre_run` の要素は
  `run_id_or_null` が当該 attempt の `actual_runs[].run_id` を指す。
- **`recovered` に相当する boolean field を持たせない。**
- `stat_before[]` / `stat_after[]` は正常時 8 要素 (`user, nice, system, idle, iowait, irq,
  softirq, steal`)。**9 要素以上は拒否する** (`guest` / `guest_nice` を足さない)。
  8 要素に満たない raw も `*_raw` として保存する。
- **`malformed_reason` は、raw から再計算した事象が存在するとき非 null 必須**であり、
  その値は**次の評価順序で最初に成立した事象**と exact 一致しなければならない。
  raw が整形式なら null とする。

```text
1. short_columns        いずれかの側の cpu 集計行が 8 列に満たない
2. negative_delta       いずれかの列の差分が負
3. nonpositive_total    total <= 0
4. window_out_of_range  窓長が 10.000 ± 0.100 秒の外
```

  この field は受理集合を**狭める方向にだけ**効く。

## 5. `reason_code` の条件分岐 (追補 A `a04` 準拠)

`completed` の意味は attempt の種別で異なる。

| `reason_code` | 要求する条件 |
|---|---|
| `completed` (性能 attempt、`cluster_slot_or_null` 非 null) | `allocation_id` 非 null、`performance_started_marker` 非 null、`failure_evidence == null`、当該 attempt の actual run が**その `cluster_slot` に属する 36 planned run**と完全双射 |
| `completed` (検証 attempt、`cluster_slot_or_null == null`) | `allocation_id` 非 null、`performance_started_marker == null`、`failure_evidence == null`、当該割当てを指す `correctness_evidence[]` が 6 件、`liveness[].probe == liveness_run` が 6 件、`actual_runs[]` は 0 件 |
| `pre_performance_infra_failure` | `performance_started_marker == null` **かつ** 当該 attempt を参照する `actual_runs[]` が **0 件** **かつ** `environment_observations[]` から `a03` の不成立・malformed が **1 件も導けない** **かつ** `failure_evidence` 非 null |
| `post_performance_failure` | §5.1 の 3 経路のいずれか 1 つ以上を満たし、`failure_evidence` 非 null |
| `correctness_anomaly` | `replaces_attempt_id == null` (終端 reject)、`failure_evidence.kind == correctness` |

### 5.1 `post_performance_failure` の 3 経路

```text
経路 1: performance_started_marker が実在する
経路 2: 当該 attempt を参照する actual_runs[] が 1 件以上実在する (性能 run の raw 痕跡)
経路 3: a03 不成立の証拠と、対応する environment_observations[] 要素がともに実在し、
        validator が raw から不成立を再計算できる
```

### 5.2 経路 3 の充足条件 (恒真化を避けるための拘束)

経路 3 は次を**すべて**満たすときにだけ成立する。producer の申告文字列は 1 つも入力にしない。

1. 当該 attempt の `environment_observations[]` に要素が少なくとも 1 つ存在する。
2. その要素が `stat_before_raw` と `stat_after_raw` の**両方**を持ち、いずれも実在して bytes が読める。
3. **validator が raw から不成立を再計算できる。** すなわち追補 A `a03` の fail-closed 事象
   (8 列未満 / 差分が負 / `total ≤ 0` / 窓長が `10.000 ± 0.100` 秒の外) のいずれか、
   または `cpu_busy_core_equivalents` が `[0.0, 1.0]` の外、**のどれか 1 つが raw から導ける**。
4. `monotonic_start_ns` と `monotonic_end_ns` が存在し、単調で、窓長を再計算できる。
5. `malformed_reason` が非 null なら、その値は §4.14 の評価順序で再計算した事象と一致しなければならない。
6. `scope == preflight` の要素で経路 3 を満たす attempt は、`performance_started_marker == null`
   であり、かつ `actual_runs[]` に当該 attempt を参照する要素が存在しないことを要求する。

### 5.3 置換の可否 (`a04`)

- **置換されうるのは `pre_performance_infra_failure` の attempt だけ**である。
  `post_performance_failure` / `correctness_anomaly` / `completed` の attempt を
  `replaces_attempt_id` で指す attempt が存在してはならない。
- 置換 attempt は `cluster_slot` を新設せず、**置換対象と同じ slot**を参照する。
- `a03` 不成立に起因する `post_performance_failure` は、下流で**「判定不能」一意**へ写る
  (`reject` を選ぶ裁量を持たない。追補 A `a04`)。
- **性能測定の開始後に起きた失敗を開始前の infra failure へ写してはならない。**
  写像は本節の表だけで決め、TPS・失敗した arm・残り run 数を参照しない。

### 5.4 受理集合はどちらへ動くか

前版 `R_old` に対し、本書の受理集合 `R_new` は次のとおり**拡大と縮小の両方**を含む。

```text
R_new = ( R_old ∪ { 経路 3 だけで post_performance_failure を満たす受領証 } )
              ∖ { marker 不在だが性能 raw または a03 不成立証拠を持つ attempt を
                  pre_performance_infra_failure として申告する受領証 }
```

**この事実を安全性の根拠に使ってはならない。**承認は「この差分を承認する」ものとして扱う。
拡大に伴って新たに開く偽造余地は §9 に明記する。

## 6. cross-field 制約 (JSON Schema だけでは閉じない。固定 semantic validator が再計算する)

### 6.1 ID と参照整合性

- `run_id` / `attempt_id` / `allocation_id` は受領証内で一意。
- `actual_runs[].{attempt_id, allocation_id, run_id}`、`liveness[].allocation_id`、
  `correctness_evidence[].run_scope.allocation_id`、`attempts[].{replaces_attempt_id,
  parent_attempt_id, allocation_id}` はすべて対応する集合の要素でなければならない (dangling 禁止)。
- `attempts[]` は durable submission intent の全 attempt を **exact に被覆**する。
- qsub が失敗した attempt も **row を省略できない**。
- **`allocations[]` は `allocation_role == verification` をちょうど 1 件持つ。**
  同一 study の別 stage の受領証は、同じ `allocation_id` と同じ bytes でその 1 本を記録する。
- 全参照は自 stage に閉じる (`cluster_slot` は stage-local。§0.1)。

### 6.2 planned ↔ actual と完全性

- 性能 attempt の `completed` だけが、その `cluster_slot` の 36 planned run に対する**完全双射**を
  要求される。
- 失敗 attempt の actual run 列は当該 slot の planned schedule に対する**厳密な prefix** であり、
  failure evidence pointer を伴う。**欠けた run を後から補って双射を成立させることを禁じる。**
- `consumed_cluster_slots` の各 slot について、`completed` の性能 attempt は**高々 1 つ**である。
- 検証割当ての attempt が `completed` の受領証では、`consumed_cluster_slots` の各 slot について
  `performance_cluster` 割当てが **1 件以上**なければならない (置換は同じ slot で新しい割当てを消費する)。
  検証割当てが失敗した stage では性能割当てが 0 件でよい。
- すべての `performance_cluster` 割当ての `cluster_slot_or_null` は `consumed_cluster_slots` の
  要素でなければならない。

### 6.3 絶対規律 1 (trace / perf の分離) と申告値の照合

- `arms.*.compile` は `trace_enabled: false` / `analysis_enabled: false` / `cmake_cache` の 2 値 0。
- `correctness_evidence[].build.compile` は両者 true / `cmake_cache` の 2 値 1。
- **申告値を単独で信用しない** — validator は次の 3 者を再読して一致を要求する。
  1. `configure_argv[]` 中の `-DCCBENCH_TRACE=` / `-DCCBENCH_ADD_ANALYSIS=` (または同等の macro 定義)、
  2. `compile_commands` 実体に現れる当該 TU の compile argv、
  3. `cmake_cache` の申告値 (`CMakeCache.txt` 由来)。
  1 つでも食い違えば拒否する。
- `correctness_evidence[].build.binary.sha256 ≠ arms.<同 arm>.binary.sha256`。
- `correctness_evidence[].run_scope.allocation_id` は `verification` 割当てを指す。

### 6.4 `a02` の待機と `a07` の argv 照合

- `preceding_wait.required_s` は境界の種別で決まる (`arm_gap` 30 / `block_gap` 60 /
  `workload_switch` 60 / cluster 最後の run の後は待機を置かない)。
- validator は `monotonic_end_ns − monotonic_start_ns` から実待機を再計算する。
  **adaptive wait は禁止**であり、実行時の延長・短縮を受理しない。
- **`actual_runs[].argv_raw` の bytes を、当該 workload の計画 argv (`driver_argv[]`) と
  exact 比較する。** `argv_sha256` はその digest であり、単独では権威にならない。
- **各 run log の `#FLAGS_` 行と `ShowOptParameters()` 行を、`effective_flags` /
  `opt_parameters` の exact map として照合する** (追補 A `a07`)。一致しなければ受理しない。

### 6.5 `a03` の観測窓の完全性

- 性能 attempt の `completed` は観測窓を**ちょうど 36 個**持つ (`scope == preflight` が 1 個、
  `scope == pre_run` が 35 個)。失敗 attempt は実行した run 数に対応する prefix を持つ。
- 各窓の窓長は `10.000 ± 0.100` 秒。観測終了から当該 run の exec までの間隔は `5` 秒以内。
- **観測窓と exec の間に他の作業・任意待機を挟まない。**
- `cpu_busy_core_equivalents = 48 × (total − Δidle) / total` を raw から再計算し、
  `[0.0, 1.0]` を許容範囲とする。不成立時の再観測・窓の取り直しは受理しない。

### 6.6 `a09` の schedule 再導出と canonical bytes

`schedule_table` の bytes は次の形だけを許す。validator はこの bytes をゼロから再導出し、
`schedule_sha256` と実体の両方を照合する。

```text
- 文字符号は UTF-8、改行は LF (CRLF 禁止)、行末に空白を置かない。最終行にも LF を置く。
- 1 行目は固定の header 行: cluster_slot<TAB>workload<TAB>block_index<TAB>permutation
- 2 行目以降は 1 行 1 block。field 区切りは TAB (0x09) 1 文字。空白 padding を置かない。
- block_index は **workload-local の 1..6**。
- 行の並びは (cluster_slot 昇順、先行 workload を先に、block_index 昇順)。
  先行 workload は slot の偶奇で決まる (奇数 slot は W2 先行、偶数 slot は W1 先行)。
- cluster_slot は 1..13 の十進 ASCII (符号なし・先頭ゼロなし)、block_index は 1..6 の同形式、
  workload は W1 | W2、permutation は SDX|SXD|DSX|DXS|XSD|XDS。
- 行数は 1 + 13 × 12 = 157 行 (13 slot × 2 workload × 6 block)。
```

block 順は追補 A `a09` の `key(j, w, p)` を再計算して定める。実 TPS・失敗理由・runtime 乱数を
入力にしない。**置換 attempt は新しい slot を作らず、置換対象と同じ slot の schedule を使う。**

### 6.7 `a13` の予約 — append-only 全履歴検査 (R3 (a))

`kind == alpha_reservation` の `ledger_evidence` に対し、validator は次をすべて行う。

1. shallow repository・replace ref・graft を拒否する。
2. `family_root` から `measurement_checkout.repository_head` まで、台帳 path の全世代を
   `--full-history --reverse` で走査する。
3. 台帳の導入が exact 1 回であり、mode が regular (100644) であることを要求する。
4. **各世代の blob が直前世代の blob の byte-prefix である**ことを要求する。削除・truncate・
   既存行の編集・並べ替え・rename/copy・delete-and-recreate を拒否する。
5. JSONL の各行を duplicate-key 拒否つきで parse し、canonical bytes と末尾 LF を照合する。
6. `(family_root, ordinal)` の**全履歴一意性**、本 study の `k = 1`、解放 entry・tombstone の
   不在を検査する。
7. `reservation_entry_sha256` と、当該行が**初めて出現した** `reservation_commit` を再導出する。
8. resolver・受領証 validator・材料 report の consumer が**それぞれ独立に全履歴を再走**し、
   受領証の現 tip 申告を信用しない。

**保証境界 (manifest / resolver / 材料 report で byte 同一の逐語を用いる):**

> この保証は、指定された一つの canonical local main、その Git common directory、
> `tools/dev_wave_land.py` を通り同一 land lock 下で取り込まれた予約履歴、およびその全履歴を
> 毎回再検査する trusted resolver / report の範囲に限る。独立 clone、別 common directory、
> 権威台帳外の投入、履歴を共有しない writer、同一権限の非協調 writer、canonical main の外で
> 作られた競合予約は保証しない。

### 6.8 消費する cluster slot

- `study_stage == pilot` の受領証は `consumed_cluster_slots` が **exact `[1,2,3,4,5,6,7,8]`**
  でなければならない (§10 の閉包 1)。
- `study_stage == main_run` では昇順・重複なしの 1..13 の部分集合とし、要素数は `J` に一致する。
- 当該受領証の全 attempt / allocation / actual run の `cluster_slot` は
  `consumed_cluster_slots` の要素に限る。
- 予備 2 本は**母数に合算しない**。置換 attempt は同一 slot を再利用するため新しい slot を消費しない。

### 6.9 時間予算 (`a01` / `a06`) と phase 写像

追補 A `a01` の予算行を phase へ次のとおり写す。**`observation` / `decision` / `marker` は
`preflight` の内側 (nested) であり、直列総和には preflight を 1 回だけ数える。**

```text
allocation_role == performance_cluster:
    preflight   cap 180   sub_cap 150   (admission・環境証明・schedule 導出・binary hash 検証)
      observation cap 10                 (a03 の観測窓 [150,160))
      decision    cap 5                  ([160,165))
      marker      cap 5                  ([165,170)。TERM_at = 170)
    run         cap 1920                 (性能 run 540 + arm 間待機 720 + block 間待機 660)
    teardown    cap 300                  (raw parse・受領証生成・phase 完全性検証 180 + 後片付け 120)
    直列総和 = 180 + 1920 + 300 = 2400 = a01 (A) の非余裕小計

allocation_role == verification:
    staging          cap 180
    build            cap 1440
    build_post       cap 360
    correctness_run  cap 360
    evidence         cap 180
    teardown         cap 120
    直列総和 = 2640 = a01 (B) の非余裕小計
```

- 直列総和は `internal_deadline_s` 以下でなければならない (主経路 3300、予備経路 4800)。
- `internal_deadline_s + scheduler safety = requested_walltime_s`
  (主経路 `3300 + 300 = 3600`、予備経路 `4800 + 600 = 5400`、検証割当て `3300 + 300 = 3600`)。
- `phase_events[]` から各 phase の実 elapsed を再計算し、cap 超過を拒否する。
  cap は phase 単位に課し、`SIGTERM` は `cap − 10` 秒、`SIGKILL` は `cap` の時点とする。
- 同一割当て内のすべての `monotonic_ns` は単調でなければならない
  (`started_at ≤ phase_events ≤ ended_at`、観測窓・run・marker の時刻も含む)。

### 6.10 受領証 writer の認可と pointer の実在

- **受領証を永続化する関数自体**が `PreregBinding` を必須 keyword-only で受け、同じ snapshot の
  受領証と binding の三つ組・`measurement_head` を照合してから publish する。
  別経路の writer が受領証を publish できてはならない。
- すべての `fileRecord` / `blobRef` について、validator は pointer の実在、`size` の一致、
  `sha256` の一致を確認する。読取は §1 のとおり単一 fd / snapshot で行い、
  各 path component を `O_NOFOLLOW` で辿り、symlink を拒否する。

## 7. 機械可読 schema の要件

- **dialect は JSON Schema draft-07** (`"$schema": "http://json-schema.org/draft-07/schema#"`)。
  repo の既存受領証 schema (`orchestrator/qualification/t126_final_receipt_schema.json` 等) と
  同じ dialect であり、検査実体も同一系統を使う。
- 参照は `definitions` + `#/definitions/...` の JSON pointer だけを使う。**外部 `$ref` を持たない。**
  `$defs`・`unevaluatedProperties`・`unevaluatedItems`・`format` 依存の keyword を使わない
  (dialect 差で受理集合が動くため)。
- instance 上の**全 object schema**に `additionalProperties: false` を課し、
  全必須 key を `required` に列挙する。条件付き不在は key 省略ではなく**明示的な `null`** で表す。
- **duplicate JSON key は schema 検査の前段の parser で拒否する。**
- schema は「形」だけを担い、**§6 の cross-field 制約と §7.1 の全項目は固定 semantic validator が
  再計算する。** schema の適合を受理と読み替えてはならない。
- **conformance vectors** (正例 1 本と、§6 の各制約に対する負例 1 本以上) を実装 wave が発行し、
  その digest を approval manifest が pin する。vectors は test 資材であり本書と同じ land では
  発行しない。engine は schema と vectors の実装であって規範ではなく、
  **engine の差で受理集合が変わってはならない。**

### 7.1 draft-07 では表現できず、固定 semantic validator が担う制約 (全件)

dialect の能力上、次は schema に書けない。**書けないことを schema の側で偽装しない** —
これらは semantic validator の必須責務として実装 wave が持つ。

```text
(1)  配列内で「種別ごとにちょうど N 件」。**件数の条件は §4.10 / §4.11 / §5 のとおり
     attempt の帰結に従属する** — 無条件に 6 件を要求してはならない。
     - attestations[] の profile_kind == expected が 1 件、observed が 1 件以上 (無条件)
     - **検証割当ての attempt が `completed` の受領証に限り**、correctness_evidence[] が 6 件で
       (arm, workload) を過不足なく覆い、liveness[] の probe == liveness_run も 6 件で同じ被覆を持つ。
       検証割当てが失敗した stage では 0〜5 件を正当な受領証として受理する
     - admission_telemetry[] の kind ごとの必須件数 (§4.12。stage に従属する)
(2)  ordinal の 1 起点連番・欠番なし (全配列)、および
     **`position == 1` と `predecessor_arm == START` の同値** (双方向。§4.8)
(3)  field 単位の一意性 — errata[].erratum_id、run_id / attempt_id / allocation_id、
     binary_rehash[] の (point, arm)、dependency_pins[].name の 5 件被覆
(4)  §4.5 / §4.8 の値が追補 A a07 / a08 / a09 の逐語と一致すること
(5)  planned_execution.runs[] の件数が 36 × |consumed_cluster_slots| であること、
     cluster_slots[] が schedule 表と 1 対 1 であること
(6)  allocation_role ごとの phase 閉集合の切り替えと phase_caps の件数・値 (§6.9)
(7)  binary_rehash[] の到達 point 条件 (§4.7) と verification 割当ての 0 要素
(8)  reason_code の分岐条件すべて (§5) — marker の有無、actual run 件数、a03 不成立の導出、
     36 run 双射、置換可能性 (§5.3)、検証 attempt と性能 attempt の区別
(9)  attempts[].cluster_slot_or_null と allocations[].allocation_role の整合
(10) stat_before[] / stat_after[] の実列数と malformed_reason の再計算一致 (§4.14 の評価順序)
(11) translation_units の key の POSIX 再正規化一致、base_tree_sha の再導出
(12) 申告値と実体の 3 者一致 (§6.3 の argv macro / compile_commands / CMakeCache)
(13) argv_raw と計画 argv の exact 比較、run log の #FLAGS_ / ShowOptParameters の exact map (§6.4)
(14) pointer の実在・size / sha256 一致・単一 fd / snapshot・symlink 拒否 (§6.10)
(15) 同一割当て内の monotonic ordering (§6.9)
(16) intent_ref / performance_started_marker の create-only 性 (§4.13)
(17) a13 台帳の append-only 全履歴検査 (§6.7)
(18) 時間予算の算術と実 elapsed の cap 超過検査 (§6.9)
(19) receipt_schema.sha256 が approval manifest の pin と一致すること (§4.2)
(20) duplicate JSON key の拒否 (parse 前段)
```

## 8. 否定検査 (実在 field だけを列挙する)

消費側が次のいずれかを**受理条件の入力**に使ったら落ちるテストを置く。prose の禁止だけにしない。

```text
declared_use_class
attempts[].reason_code == "completed"
attempts[].qsub_result.returncode
allocations[].exclusivity
admission_telemetry[].fixed_inputs
preregistration.composed_core_sha256
planned_execution.schedule_sha256
arms.*.compile.trace_enabled / analysis_enabled / cmake_cache
```

いずれも producer が書く申告値であり、受理は validator の再計算だけが決める。

## 9. 本書が保証しないこと

- **★ 経路 3 は、不利な実 run を「実行しなかった」に見せかける経路を開く。**
  producer は preflight 観測窓に**自分が作った raw** を置けば、marker も性能 run も持たない attempt を
  正当な `post_performance_failure` として記録できる。これは 7 列などの malformed な raw に限らない —
  **8 列すべてが揃い差分も非負で窓長も正しく、値だけが `[0, 1.0]` の外にある raw** も同じ経路を
  満たす (例: `total = 100`、`busy = 5` なら `48 × 5 / 100 = 2.4`)。
  §5.2 の 6 条件は「raw から失敗が導けること」までしか強制できず、
  **その raw が実際のカーネル出力かどうかは producer 権限内では判別できない。**
  certified 値を直接上げることはできない (固定 `J` の完全性 gate が別に効く) が、
  **試行台帳における「この試行は実行されなかった」という事実そのものが偽造可能になる。**
  閉じるには producer 権限外の collector が raw を独立に採取する必要があり、それは本書の射程外である。
  **この残余は承認時に明示的に引き受けられたものとして扱う。**
- **単独性は保証しない。** 計算ノードは専有割当てを保証せず、外部 process の情報は診断に留まる。
  `exclusivity` は生出力 pointer だけを持ち、boolean を持たない。
  「単独性を確認した」と書けるのは検査を実行した事実だけであり、単独であったことは保証されない。
- **台帳の外で走らせた投入は見えない。**
- **producer が実際とは異なる bytes や schedule で走らせながら整合した受領証を作る偽造は
  検出できない。**受領証の三つ組と `measurement_head` の照合が検出するのは「producer が書いた
  2 つの文書の食い違い」であり、実測 checkout の一致ではない。`a05` の exec witness と 3 点再 hash は
  検出の敷居を上げるが、外部の時刻根拠なしには閉じない。
- **`a03` の恒真化は静的検査では防げない。** 本書は raw counter の保存を強制することで再計算を
  **可能にする**が、実装が実際に再計算することは保証しない。
- **`a13` の全履歴検査は §6.7 の保証境界の外では何も保証しない。**
- **schema の適合は受理ではない。** §7.1 の 20 項目は schema の外にあり、
  semantic validator が実装されるまで**一つも発火しない。**
- **本書は実装ではない。** schema を機械化する producer / validator は未実装である。

## 10. 本書が新設した閉包 (承認対象。承認済み文書から一意には導けない選択)

次の 8 件は、承認済み文書 (core §12、追補 A `a01`〜`a13`、D162 / D262〜D264) から**一意には
導けない**。閉じなければ producer が受理条件を選べるため本書が閉じたが、**選択であることを明示する。**
承認は、この 8 件を含めて承認するという意味になる。

| # | 閉包 | 導出の根拠 | 反転した場合 |
|---|---|---|---|
| 1 | `study_stage == pilot` の `consumed_cluster_slots` を `[1..8]` に固定 | `a09` は slot を 1 起点で定義し、任意の prefix `1..r` で先行 workload の差を `⌈r/2⌉ − ⌊r/2⌋ ≤ 1` に保つ設計 (= 先頭から連続消費が前提)。`a10` は適格 pilot を 8 本とする | 固定しないと producer が結果を見て 8 本を選べる。**8 本の identity を pilot 前に別の形で固定する必要がある** |
| 2 | `exclusivity.method` を `{node_local_process_scan, scheduler_accounting}` に閉じた | core §12 は単独性検査の記録を要求するが手法を列挙しない。この 2 つは環境 runbook が実際に取れる検査である | 別手法の証拠が未知 enum として拒否される。enum を開くと producer が任意の「検査」を名乗れる |
| 3 | 割当ての phase 閉集合を役割別 2 種にした | `a01` (A) は preflight / run / 待機 / parse / 後片付け、(B) は staging / build / build 後処理 / correctness / evidence / 後片付け。`a03` が preflight 内の 4 区間を逐語で固定する | 単一 enum に戻すと検証割当てが架空の marker / run phase を書かされる |
| 4 | schedule 表の canonical bytes (TSV・header・157 行・並び順) | `a09` は「canonical bytes の SHA-256 を受領証へ記録する」と要求するが serialization を定めない。定めないと 2 実装が同じ schedule で別 digest を出す | 別 serialization が拒否される。定めないと `schedule_sha256` が独立再導出できない |
| 5 | `schema_version` の literal `t139-receipt/v1` | repo の既存受領証 schema が同型の const を持つ (`t126-qualification-final-receipt/v1`) | 版の識別子が実装依存になる |
| 6 | `scheduler_request_id` / `qsub_result{returncode, raw}` の新設 | core §12 は「割当て ID・会計痕跡」と「全 attempt の保存」を要求し、前版は「qsub 失敗 attempt の row を省略できない」と課す。scheduler 側の識別子と rc は raw な実行事実である | qsub 失敗の記録が pointer だけになり、否定検査の対象 field が消える |
| 7 | `failure_evidence.kind` の 5 値 | `a04` が写像する失敗の種別 (`a03` 環境 / scheduler / driver / collector / correctness) に対応する | 種別を持たないと failure の原因帰属が pointer の中身に依存する |
| 8 | `attestations[].profile_kind` の `{expected, observed}` | 既存 env attestation 実装が期待 profile と観測 profile の 2 系統を持つ | 環境証明の 2 系統の区別が受領証から失われる |
