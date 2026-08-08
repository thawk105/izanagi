# [T-139] 段 A 記録項目 (受領証 closed schema) の案 — 裁定 gate 提出用

```text
authority: none
default_effect: no-state-change
```

本書は **提案**である。採用されていない。可変状態の正本は `docs/worklog.md` 末尾であり、
記録項目の確定は D229 決定 (7) と事前登録 §11 段 A が定める**単独の裁定 gate** の対象である。
本書はその gate へ提出する案であり、実装ではない (本 wave はコードを 1 行も land していない)。

対応する事前登録: `output/insights/2026-08-07_t139-mainrun-design/preregistration.md` §12。

## 0. 設計原則 (D162 の直接適用)

- producer が書けるのは **raw な実行事実と証拠 pointer**、および**利用意図を示す閉集合の種別**だけである。
- 適格性状態・pairing の成否・受理状態・validator の identity / 結果は **未知 field として拒否**する。
- **本 schema のどの field も、単独では適格性の入力にならない。** 消費側は producer の申告値を読まず、
  信頼された validator を同一呼出しの中で再実行する (D162 決定 (4))。
- 検査は単一 fd / snapshot で読み、hash と parse を同一 byte buffer に対して行う (D162 決定 (5))。symlink は拒否する。

## 1. top-level の exact key (18)

```text
schema_version  study_id  declared_use_class  study_stage
series_id  parent_series_id
preregistration  environment  measurement_checkout  dependency_pins
arms  allocations  planned_execution  actual_runs
correctness_evidence  liveness  admission_telemetry  attempts
```

`additionalProperties: false` を top-level と**全 nested object**へ課す。

### §12 との対応

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

## 2. 段 3 の敵対検証を反映した追加要件

段 2 の初版は key 閉包しか持たず、レンズ A/B が計 4 系統の穴を指摘した。反映後の要件は次のとおり。

### (a) 絶対規律 1 — trace / perf の分離を再計算可能にする (レンズ A 所見 6)

初版は `arms.*.compile` に性能 arm の identity/argv しか持たず、`correctness_evidence[].trace_binary` を
性能 binary と結んでいなかった。これでは「性能測定が trace-disabled、correctness が trace-enabled の
**別ビルド・別 run**」であることを受領証から再計算できない。

- `arms.*.compile` に `trace_enabled: false` を**必須**とし、`argv` の中の trace マクロ定義と整合させる。
- `correctness_evidence[]` に独立の `build` object (`source`, `compile{identity_sha256, argv, trace_enabled: true}`,
  `binary{path, sha256}`) を持たせる。
- **非同一性を schema 制約として課す** — `correctness_evidence[].build.binary.sha256`
  は同じ arm の `arms.*.binary.sha256` と一致してはならない。
- `correctness_evidence[]` に `run_scope` を持たせ、性能測定と同じ `allocation_id` / `run_id` を指してはならない。

先例: `orchestrator/qualification/artifacts.py` は trace / perf hash の相違と、verifier がその trace hash を
使ったことまで検査している。同型の制約をここでも置く。

### (b) 条件付き制約と参照整合性 (レンズ A 所見 8)

key 閉包だけでは「欠測」と「存在しない実行」を後段が区別できない。次を課す。

- `schema_version` は const。ID・hash・path は型と正規表現で拘束する (40 桁 / 64 桁 lowercase、repo 相対 path)。
- `arms` は `stock` / `mode1` / `modeX` の exact 3 arm。1 cluster は 6 反復・3 arm の全 6 順列を各 1 回
  (事前登録 §7) であり、`planned_execution.runs[]` は 1 割当てあたり 6 件。
- ID の一意性 — `run_id` / `attempt_id` / `allocation_id` は受領証内で一意。
- 参照整合性 — `actual_runs[].run_id` は `planned_execution.runs[].run_id` の集合と**双射**、
  `actual_runs[].attempt_id` と `allocations[].allocation_id` は `attempts[]` の集合へ含まれる。
- `attempts[].reason_code` による条件分岐 —
  `completed` は `allocation_id` / `measurement_started_at` を要求し、
  `pre_measurement_infrastructure` は `measurement_started_at` が `null` であることを要求し、
  `post_measurement_failure` は `null` を**許さない**。
  `correctness_anomaly` は `replaces_attempt_id` を持てない (終端 reject であり置換されない、事前登録 §9)。
- qsub が失敗した attempt は `allocation_id` などを `null` にできるが、**row 自体を省略できない**。

### (c) evidence-only の明示と、下流での権威化の禁止 (レンズ A 所見 10)

- `correctness_evidence[].outputs` は**再実行可能な pointer** (path + size + sha256) に限り、
  verdict 文字列や boolean を置ける型を持たない。
- `declared_use_class` の 4 値 `{official, exploration, qualification, dry}` は**利用意図**であり、
  `qualification` は「適格性審査へ提出する」の意味で**合格宣言ではない** (D162 決定 (1))。
  `official` も「正式用途の意図」以上を意味しない。
- **否定検査を必須にする** — 消費側が `declared_use_class`、`admission_telemetry[].returncode`、
  `attempts[].reason_code == "completed"`、`allocations[].exclusivity` のいずれかを受理条件の入力に
  使ったら落ちるテストを置く。prose の禁止だけにしない。

### (d) 失敗投入を raw に残す authority (レンズ B 所見 7)

事前登録 §13 の否定検査 1 (失敗投入を台帳と raw の双方から落とす) は、受領証 schema だけでは閉じない。
次が同じ実装単位に要る。

- qsub より**前**に durable な submission intent を書く (create-only)。既存先例は
  `tools/pegasus/submit_t126_qualification.sh` が qsub 前に intent と reservation を書き、
  qsub invocation claim を残してから実行する形である。
- job 側 preflight の reject を回収する collector。job 側の最初の書込みより前に preflight が走るため、
  収集経路が無いと reject した attempt が raw 母集団から消える。
- `attempts[]` は intent の全 attempt を **exact に被覆**する (部分被覆を許さない)。

### (e) 認可を受領証の実 writer に置く (レンズ B 所見 3、T-643 (i))

初版は `qsub` を行う関数にだけ binding を必須化し、受領証を実際に書く `publish_raw_receipt` は
binding を受けていなかった。これは T-609 が否定した「呼び手側の認可」の再現である。

- **受領証を永続化する関数自体**が `PreregBinding` を必須 keyword-only で受け、
  同じ snapshot の受領証と binding の三つ組・`measurement_head` を照合してから publish する。
- 先例: `orchestrator/qualification/artifacts.py` の emit sink が capability を再検査する形。

## 3. 本案が保証しないこと

- **台帳の外で走らせた投入は見えない。**
- **producer が実際とは異なる bytes や schedule で走らせながら整合した受領証を作る偽造は検出できない。**
  受領証の三つ組と `measurement_head` の照合が検出するのは「producer が書いた 2 つの文書の食い違い」であり、
  実測 checkout の一致ではない。これは事前登録 §15 の明示する非保証であり、
  T-643 (ii) が「完全な偽造検出は見送り (D205)、pilot では人間確認を併用」と裁定した範囲と一致する。
- **a03 の恒真化は静的検査では防げない** — 「`allocation_observation` と名乗りながら定数を返す実装」
  「有限だが実現値を必ず含む範囲」は、raw observation からの再計算 (段 C validator) を要する。
