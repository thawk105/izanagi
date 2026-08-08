# [T-139] 段 A 記録項目 — 受領証 schema の**要件文書** (裁定 gate 提出用)

> **呼称について。** 本書は「closed schema」そのものではない。
> `additionalProperties: false` を全 object へ課すという**要件**を定める文書であり、
> 完全な機械可読 schema (全 nested object の exact key・型・必須性・配列長・cross-field 制約) は
> 本書の §3.1 が定めるとおり producer 実装 wave が 1 枚の blob として発行する。
> 段 6 の敵対レビュー 2 本と焦点再レビューが、初版の「closed schema」という呼称が
> 実体を過大に表すと独立に指摘したため改めた。

```text
authority: none
default_effect: no-state-change
document_kind: receipt_schema_proposal
```

本書は 2026-08-08 の `output/insights/2026-08-08_t139-producer-adjudication/record-items.md` の
**後継**である。前版に対し、段 3 の敵対レンズ 2 本が指摘した穴と、追補 A の `a01`〜`a09` を
validator が再計算するために必要な nested field を反映した。

**本書は提案であって採用ではない。** 記録項目の確定は D229 決定 (7) と事前登録 §11 段 A が定める
**単独の裁定 gate** の対象である。対応する事前登録は
`output/insights/2026-08-07_t139-mainrun-design/preregistration.md` §12、
および同ディレクトリの `addendum-a.md`。

**top-level の key は 18 のまま増やさない。** 追加はすべて既存 key の内側 (nested) に置く。
**凍結後・実走時に未知の nested field を自由追加すること、および 19 個目の top-level key を
足すことは余剰 field 違反である。**承認前の本書で nested schema を完成させるのは余剰違反ではない。

---

## 0. 設計原則 (D162 の直接適用。前版から不変)

- producer が書けるのは **raw な実行事実と証拠 pointer**、および**利用意図を示す閉集合の種別**だけである。
- 適格性状態・pairing の成否・受理状態・validator の identity / 結果は **未知 field として拒否**する。
- **本 schema のどの field も、単独では適格性の入力にならない。** 消費側は producer の申告値を読まず、
  信頼された validator を同一呼出しの中で再実行する (D162 決定 (4))。
- 検査は単一 fd / snapshot で読み、hash と parse を同一 byte buffer に対して行う (D162 決定 (5))。
  symlink は拒否する。

## 1. top-level の exact key (18。前版から不変)

```text
schema_version  study_id  declared_use_class  study_stage
series_id  parent_series_id
preregistration  environment  measurement_checkout  dependency_pins
arms  allocations  planned_execution  actual_runs
correctness_evidence  liveness  admission_telemetry  attempts
```

`additionalProperties: false` を top-level と**全 nested object**へ課す。

### §12 との対応 (前版から不変)

| 事前登録 §12 の必須項目 | key |
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

---

## 2. 前版から変えた点 (段 3 の敵対レンズが指摘した穴)

### (a) `planned_execution` の run 数を訂正した — **前版は誤り**

前版は `planned_execution.runs[]` を「1 割当てあたり 6 件」としていた。**これは誤りである。**
事前登録 §7 は「cluster 内は 6 反復、3 arm の全 6 順列を各 1 回」とする。1 つの順列は 3 arm の
**3 run** なので、

```text
1 workload = 6 permutation block × 3 arm = 18 run
1 cluster  = 2 workload × 18          = 36 run
1 cluster  = 12 block
```

である。6 件では全順列の 1/6 しか表せず、正常な cluster を拒否するか、欠落した 30 run を
見えなくする。段 3 の 2 レンズが独立に、位置ごと 2 回・直前 arm ごと 2 回の数え上げから
36 run 解釈だけが core §7 の均衡条件を満たすことを確認した。

`planned_execution.runs[]` の各要素は次を必須とする。

```text
run_id  cluster_slot  workload  block_index  permutation
planned_ordinal  position  predecessor_arm  arm
preceding_wait { kind, required_s }
```

`predecessor_arm` は block 先頭で `START`。`permutation` は `{SDX,SXD,DSX,DXS,XSD,XDS}` の enum。

### (b) planned ↔ actual を**無条件の双射にしない** — 前版は捏造を促していた

前版は `actual_runs[].run_id` を `planned_execution.runs[]` と無条件に双射としていた。
これは post-performance failure の正当な prefix を拒否する一方、欠けた run の捏造を促す。

- `attempts[].reason_code == "completed"` の attempt だけ、36 run の**完全双射**を要求する。
- 失敗 attempt は、planned schedule に対する actual run の**厳密な prefix** であることを要求し、
  加えて failure evidence pointer を必須とする。
- 欠けた run を後から補って双射を成立させることを禁じる。

### (c) 絶対規律 1 — trace / perf の分離を再計算可能にする (前版から継続)

- `arms.*.compile` に `trace_enabled: false` と `analysis_enabled: false` を**必須**とし、
  `argv` 中のマクロ定義および `CMakeCache.txt` の `CCBENCH_TRACE` / `CCBENCH_ADD_ANALYSIS` と整合させる。
- `correctness_evidence[]` に独立の `build` object
  (`source`, `compile{identity_sha256, argv, trace_enabled: true, analysis_enabled: true}`,
  `binary{path, size, sha256}`) を持たせる。
- **非同一性を schema 制約として課す** — `correctness_evidence[].build.binary.sha256` は
  同じ arm の `arms.*.binary.sha256` と一致してはならない。
- `correctness_evidence[].run_scope` は性能測定と同じ `allocation_id` / `run_id` を指してはならない
  (追補 A `a01` は correctness を**別割当て**に置く)。

### (d) 条件付き制約と参照整合性 (前版から継続、enum 名を訂正)

- `schema_version` は const。ID・hash・path は型と正規表現で拘束する
  (40 桁 / 64 桁 lowercase hex、repo 相対 path)。
- `arms` は `stock` / `mode1` / `modeX` の exact 3 arm。
- ID の一意性 — `run_id` / `attempt_id` / `allocation_id` は受領証内で一意。
- `actual_runs[].attempt_id` と `allocations[].allocation_id` は `attempts[]` の集合へ含まれる。
- **`reason_code` の enum を probe / core の名前へ揃える** (前版は別名だった):
  `pre_performance_infra_failure` / `post_performance_failure` / `correctness_anomaly` / `completed`。
- 条件分岐 — `completed` は `allocation_id` と `performance_started` marker を要求し、
  `pre_performance_infra_failure` は marker が不在であることを要求し、
  `post_performance_failure` は marker の実在**または**性能 run の raw 痕跡の実在を要求する。
  `correctness_anomaly` は `replaces_attempt_id` を持てない (終端 reject であり置換されない)。
- qsub が失敗した attempt は `allocation_id` 等を `null` にできるが、**row 自体を省略できない**。

### (e) evidence-only の明示と、下流での権威化の禁止 (前版から継続)

- `correctness_evidence[].outputs` は**再実行可能な pointer** (path + size + sha256) に限り、
  verdict 文字列や boolean を置ける型を持たない。
- `declared_use_class` の 4 値 `{official, exploration, qualification, dry}` は**利用意図**であり、
  `qualification` は「適格性審査へ提出する」の意味で**合格宣言ではない**。
- **否定検査を必須にする** — 消費側が `declared_use_class`、`admission_telemetry[].returncode`、
  `attempts[].reason_code == "completed"`、`allocations[].exclusivity` のいずれかを
  受理条件の入力に使ったら落ちるテストを置く。prose の禁止だけにしない。

### (f) 失敗投入を raw に残す authority (前版から継続)

- qsub より**前**に durable な submission intent を書く (create-only)。
- job 側 preflight の reject を回収する collector を同じ実装単位に含める。
- `attempts[]` は intent の全 attempt を **exact に被覆**する (部分被覆を許さない)。

### (g) 認可を受領証の実 writer に置く (前版から継続)

- **受領証を永続化する関数自体**が `PreregBinding` を必須 keyword-only で受け、
  同じ snapshot の受領証と binding の三つ組・`measurement_head` を照合してから publish する。

---

## 3. 追補 A を validator が再計算するために足りない nested field

前版には無く、本確定案が追加するもの。**すべて既存 18 key の内側に置く。**

| 追補 A の field | 追加する nested schema |
|---|---|
| `a01` / `a06` | `allocations[].{allocation_role, path_choice, requested_walltime_s, internal_deadline_s, phase_caps[], phase_events[]}`。`allocation_role ∈ {performance_cluster, verification}`、`path_choice ∈ {primary_build_outside, fallback_build_inside}`。`path_choice` は投入前に固定した値であることを示す durable intent pointer を伴う |
| `a02` | `planned_execution.runs[].preceding_wait{kind, required_s}` と `actual_runs[].preceding_wait{kind, required_s, monotonic_start_ns, monotonic_end_ns}`。producer は `satisfied` boolean を書かず、validator が秒数を再計算する |
| `a03` | 観測は **`attempts[].environment_observations[]`** に置く (`actual_runs[]` の下に置くと、**観測が不成立で run が実行されなかった場合に記録先が存在しない**)。各要素は `{ordinal, scope ∈ {preflight, pre_run}, run_id_or_null, stat_before_raw{path,size,sha256}, stat_after_raw{path,size,sha256}, stat_before[], stat_after[], monotonic_start_ns, monotonic_end_ns, load1_diagnostic, malformed_reason_or_null}`。`stat_before/after` は `/proc/stat` の `cpu` 集計行の 8 列だが、**8 列に満たない raw も可変長 pointer (`*_raw`) として保存する** (zero-fill しない)。**`recovered` に相当する boolean field を持たせない** |
| `a04` | `attempts[].performance_started_marker{path, size, sha256, created_at_monotonic_ns}` (create-only)。`a03` 不成立は位置を問わず `post_performance_failure` へ写す (追補 A `a04` の既定)。marker が `null` の attempt に性能 run の raw 痕跡があれば validator が保守側へ倒す |
| `a05` | `arms.*.binary{path, size, sha256}`、`arms.*.built_outside_allocation{artifact_path, size, sha256}`、`arms.*.toolchain{compiler_path, compiler_version, compiler_sha256, link_argv[], dynamic_deps[], elf_interpreter}`、`actual_runs[].{binary_sha256, exec_witness{path, inode, size, sha256, monotonic_ns}}`、`allocations[].binary_rehash[]` (staging 直後 / 最初の run 前 / 最後の run 後の 3 点) |
| `a07` | `planned_execution.workloads.{W1,W2}.{driver_argv[], effective_flags{}, opt_parameters{}}`、`actual_runs[].{argv_sha256, run_log{path, size, sha256}}`。validator が run log の `#FLAGS_` 行と `ShowOptParameters()` 行を exact map として照合する |
| `a08` | `arms.*.compile{source{repo_commit, ccbench_pin, base_tree_sha, patch_path, patch_sha256}, mode_macro, configure_argv[], translation_units{}, identity_sha256, trace_enabled, analysis_enabled, cmake_cache{trace, add_analysis}}`。`translation_units` は全 TU の正規化 argv を持つ (3 TU に限定しない) |
| `a09` | `planned_execution.{schedule_seed, schedule_algorithm, schedule_sha256, cluster_slots[]}`。`schedule_algorithm` は const `"t139-a09-v1"`。置換 attempt は `cluster_slot` を新設せず置換対象と同じ slot を参照する |
| `a10` / `a11` / `a12` | `admission_telemetry[]` に、`J` 導出・`q` 導出・較正 simulation の各 receipt を raw pointer (`path, size, sha256`) と固定入力 (`B`, `seed`, `input_sha256`) つきで置く。**producer の `pass` 申告を権威にせず、validator が transcript を再計算する** |
| `a13` | `series_id` / `parent_series_id` の隣に、`admission_telemetry[]` の 1 要素として **alpha 台帳の予約証拠** — `ledger_path`, `family_root`, `ordinal`, `reservation_entry_sha256`, `reservation_commit` — を必須化する。validator は台帳を読み直し `(family_root, ordinal)` の**重複が無いこと**を確認する。**受領証の `ordinal` は自己申告であり権威ではない** |
| erratum | `preregistration.errata[]{path, commit, sha256, approval_fold_commit}`。top-level key は増やさない。**権威は approval manifest 側**であり、この配列は照合対象である |
| raw pointer の補強 | `actual_runs[].argv_sha256` だけでは明示 argv の exact 比較を再計算できない。`actual_runs[].argv_raw{path, size, sha256}` (実 argv の canonical bytes) と `arms.*.compile.compile_commands{path, size, sha256}` (build 時の `compile_commands.json` 実体) を必須化する |

---

## 3.1 本書は「完全な機械可読 schema」ではない (段 6 レビュー 2 本が独立に指摘)

本書は top-level 18 key と `additionalProperties: false` を宣言し、追補 A を validator が
再計算するのに必要な nested field を列挙するが、**全 nested object の exact key・型・必須性・
配列長・cross-field 制約を網羅した機械可読 schema ではない。**
`allocations[]`・`liveness[]`・`admission_telemetry[]`・`attempts[]`・`phase_caps[]`・
`translation_units{}`・`cluster_slots[]` などは、要求される内容を書いてあるだけで
key 単位の閉包を与えていない。

**この状態のままだと、2 つの実装が未知 field・`null`・参照整合性の扱いを違えても
本書に適合でき、同じ受領証が validator A では適格・validator B では拒否になりうる**
(適格 cluster 集合と certified 判定が実装で分岐する)。

したがって次を要求する。

- **完全な機械可読 schema (JSON Schema 相当) を pilot 投入より前に 1 枚の blob として発行し、
  その digest を `PreregBinding` に固定する。**
- 本書はその schema が満たすべき**要件**を定める文書であり、schema 自体ではない。
  schema の発行は producer 実装 wave の責務である (D234 実装境界。本 wave はコードを追加しない)。
- schema の発行時点と承認単位は `package.md` の裁定 R6 が扱う。

## 4. 本案が保証しないこと

- **台帳の外で走らせた投入は見えない。**
- **producer が実際とは異なる bytes や schedule で走らせながら整合した受領証を作る偽造は検出できない。**
  受領証の三つ組と `measurement_head` の照合が検出するのは「producer が書いた 2 つの文書の
  食い違い」であり、実測 checkout の一致ではない。これは事前登録 §15 の明示する非保証と同じである。
  `a05` の exec witness と 3 点再 hash は検出の敷居を上げるが、外部の時刻根拠なしには閉じない。
- **`a03` の恒真化は静的検査では防げない** — 「`environment_observation` と名乗りながら定数を返す実装」は、
  raw counter からの再計算 (段 C validator) を要する。本 schema は raw counter の保存を強制することで
  その再計算を**可能にする**が、実装が実際に再計算することは保証しない。
- **本書は実装ではない。** schema を機械化する producer / validator は未実装である。
