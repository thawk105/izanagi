# [T-1851] terminal 証拠の契約 v3 (段 1 版。**同 dir の `contract-v3.1.md` が supersede した**)

> **この文書は正本ではない。** 段 3 の敵対レンズ 2 本が 6 件の訂正点を出したため、段 4 で
> `contract-v3.1.md` を正本とした (規律 7 の追記訂正。本文は遡って改変しない)。
> 変更の一覧は `contract-v3.1.md` の 0.1 節、裁定は `s4-adjudication.md` にある。
> 特に 1.5 (identity の権威)、4 (E1 の入力値域)、5.2 (probe P-1 の射程)、5.3 (`not-consumed` の正例)、
> 6.1 (draft の形)、7 (`finished_at`)、9 (semantic な pin) は本文書の記述が不足している。

契約 v2 (`output/insights/2026-09-07_t1851-unit-c-launcher-raw-facts/s4-adjudication.md` 3 節) を
規律 7 に従って**追記で訂正**した版である。v2 の判定を遡って無効化しない。訂正の根拠は
`output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/` (欠陥 7 件 + 偽造 2 件、
未裁定 4 件の決着) と、本 wave の `parent-probes.md` (各条項を束縛する consumer への probe)。

**確定の条件:** 各条項には、それを束縛する consumer へ実際に通した probe の番号を付ける。
probe を通していない条項は契約に入れない。これが v2 が実体化できなかった直接の原因である。

- C1b が実体化する。C2 が供給する。D2 が再検証する。
- **land しない (D1341)。** 6 単位が揃うまで branch 上の checkpoint に留める。

---

## 0. 何を守る契約か (裁定 0)

守る対象は **「試行 proof chain に虚偽の terminal 事実が入ること」だけ**である。床値の数値は
既存の verifier と journal からの再計算が守っており、本契約はそこを守らない。

塞ぐ穴は具体的に 1 つである。正当な予約・分類・観測開始までを通常経路で作り、terminal builder
だけが任意の出力 bytes・状態・digest・主値・測り直し理由を返すと、台帳 core は形と相互整合しか
見ないためその行が hash chain に載る。`capture_attempt_registry_prefix()` がその chain head を
result v5 に載せ、live verifier / holdout freeze / ratified freeze が同じ prefix を受理する。

**現時点で certified 成果物への到達経路は 0 件である** (`assemble_result()` は v4 を出し、
holdout / ratified の top-level 検査も既定 v4 を要求する)。C1b 単独では有効化されない。

---

## 1. 証拠文書

**文書名:** `s8b-floor-terminal-evidence/v2`。canonical JSON
(`attempt_registry_core.canonical_json_bytes`、`sort_keys`、`allow_nan=False`) の LF 無し bytes。

digest = sha256(bytes) を v2 terminal 行の新 field `terminal_evidence_sha256` に載せる。
文書は `floor-attempt-registry-receipts/terminal-evidence/<digest>.json` へ create-only
(`allow_exact_retry=True`) で公開し、`_atomic_update_locked` の `prepare()` (registry staging の前)
で公開する。**v1 の event key 集合と受理集合は 1 bit も変えない。**

### 1.1 再導出面 (平文) と束縛面 (digest) を分ける [訂正 C / probe P-2]

契約 v2 は `probe_before` / `probe_after` / `campaign_record` を exact に載せると書いた。
これは **guarded writer が必ず拒否する**。証拠文書は `_write_staging()` を通り、
`assert_holdout_safe_bytes()` が holdout の三軸 conjunction を走査するためである。
`campaign_record.workload` は freeze の ycsb mapping そのもの、`run_cmd` はその argv、
`notes` と probe の stdout は同じ値の自然文であり、いずれも 3 軸を同時に含む。

**平文に載せてよいのは、E1 の 6 枝と 2 節の相互整合が実際に読む値だけである。**
測定で確かめた境界は「三軸のうち 2 軸までは通り、3 軸そろうと落ちる」で、
`holdout_id` と `cell_id` は単独では汚染しないので平文で残す。

| 面 | 載せるもの |
|---|---|
| 平文 (再導出面) | `schema_version`、`attempt_binding`、`mode`、`expected_use_perf`、`finished_at`、`session_cv_max`、`reps_expected`、`throughputs` (有限のみ)、`nonfinite_count`、`exec_failures`、`rep_integrity_failures`、`launch_failures` の件数、`failure` の `stage` と非 null 性、probe 組の `competing` と rc・stdout・stderr の**空か否か**、`campaign_record` の identity と計測 field |
| 束縛面 (digest) | `campaign_record_sha256`、`workload_sha256`、`run_cmd_sha256`、`notes_sha256`、`rep_observations_sha256`、`probe_before_sha256`、`probe_after_sha256`、`failure_message_sha256`、`launch_failures_sha256`、`perf_preflight_receipt_sha256`、`raw_output_sha256`、`report_sha256`、`observation_sha256` |

**最終 canonical bytes は既存の holdout-safe gate を必ず通す。専用 bypass は作らない。**
これは launcher が pre-output 証拠へ既に使っている規律 (`_external_evidence_sha256`) と同型で、
新しい逃がし道を作らない (規律 2)。

### 1.2 平文 field の出所と束縛

D1113 (呼び手は証拠の値を選べない) を全 field へ適用する。

| field | 出所 | 束縛 |
|---|---|---|
| `schema_version` | launcher 定数 | literal |
| `attempt_binding` | reservation + handle state | exact object。3 digest の綴りは `_AttemptState` の現物に合わせる (1.3) |
| `protocol` | reservation (normalized 全体) | `canonical_protocol_sha256(protocol) == binding.protocol_sha256` を launcher で副作用前、adapter で再検査 |
| `mode` | reservation | `{"pilot","official"}` literal。adapter が durable claim の `mode` と等値 |
| `perf_preflight_receipt_sha256` + `expected_use_perf` | reservation | `expected_use_perf == use_perf_from_receipt(receipt)`。official + receipt 非 null + True は拒否。capture kwargs `use_perf` (省略時 True) と等値 |
| `probe_before` / `probe_after` | launcher 固定 argv | 平文は `{competing, rc_is_zero, stdout_is_empty, stderr_is_empty}`。生値は digest。**`probe_after is None` ⇔ `probe_before.competing`** |
| `failure` | launcher | null または `{stage, exception_type, errno}`。`message` は digest |
| `launch_failures_count` | token (`_launch_failure_evidence` 射影) | `failure.stage == "capture"` なら 0 |
| `throughputs` | opened measurement を私有 sink の qualified 列と照合 | **有限 float だけの列** (1.4) |
| `nonfinite_count` | 正規化時に数える | int ≥ 0 |
| `reps_expected` | `protocol["reps"]` | capture kwargs `reps` と等値 |
| `exec_failures` | 私有 sink から再導出 | `campaign_record.exec_failures` と等値でのみ束縛 (3 節) |
| `rep_integrity_failures` | `s8b_floor_stats._derive_rep_integrity` | opened なら exact int、それ以外 null |
| `session_cv_max` | `protocol["session_cv_max"]` | decimal 文字列 |
| `raw_output_sha256` | launcher が `raw_output_bytes` から計算 | adapter の deferred reader 再計算と等値。`== sha256(serialize_session_line(campaign_record))` |
| `report_sha256` / `observation_sha256` | 導出 | report = raw line digest、observation = observed のときだけ `rep_observations` の canonical digest、他は null |
| `finished_at` | launcher の注入 clock (`classified_at` と同じ callable) | text |
| `campaign_record_*` | terminal builder | 1.5 の 30 key を identity / 計測 / 束縛の 3 群へ分ける |

### 1.3 `attempt_binding` の 3 digest は現物の綴りに合わせる [訂正 B / probe P-5]

契約 v2 は `observation_start_event_sha256` と書いたが、`_AttemptState` が持つのは
`classification_receipt_sha256` / `classification_event_sha256` / **`observation_event_sha256`** で、
3 つ目の綴りが違う。**契約は現物の綴りを採る。** launcher の 3 型はこの 3 digest を持たない。

### 1.4 非有限値の表現 [訂正 F / probe P-4]

契約 v2 の「null へ正規化して列に残し、かつ `len(throughputs) + nonfinite + exec == reps`」は
自己矛盾していた。v3 は次のとおりにする。

- **`throughputs` は有限値だけの列**にする。非有限の本数は `nonfinite_count` が持つ。
- 不変条件は `len(throughputs) + nonfinite_count + exec_failures == reps_expected`。
- E1 の `assess_session` へは **有限のみの列と、元の `reps_expected`** を渡す。
- **落とした本数の分だけ `reps` を減らしてはならない。** 減らすと `required_reason` が消えて
  欠測が健全な session に見える (probe P-4 で実測)。

### 1.5 `campaign_record` は exact 30 key [訂正 A / 訂正 E / probe P-3]

正本は `s8b_ratified_freeze._JOURNAL_KEYS["session"]` で、独立 trust root として exact 30 key。

```
attempt_id binary_sha256_at_measure cell_id configuration_id duration_s event
excluded_reason exclusion_class exec_failures holdout_id kind notes probe_after
probe_before records rep_integrity_failures rep_observations reps_expected retry
retry_ordinal round run_cmd seq session_cv session_median threads throughputs
trigger valid workload
```

前 wave の brief が列挙した 29 語には `binary_sha256_at_measure` が抜けていた。**上の 30 語が正本。**

- identity 群 (平文): `attempt_id` `cell_id` `configuration_id` `holdout_id` `kind` `event`
  `round` `seq` `retry` `retry_ordinal` `trigger` `records` `threads`
- 計測群 (平文): `throughputs` `reps_expected` `exec_failures` `rep_integrity_failures`
  `session_median` `session_cv` `duration_s` `valid` `excluded_reason` `exclusion_class`
  `binary_sha256_at_measure`
- 束縛群 (digest のみ): `workload` `run_cmd` `notes` `probe_before` `probe_after` `rep_observations`

identity 群は reservation と、計測群は opened / 私有 sink と、`excluded_reason` /
`session_median` / `valid` は再導出と**全件等値**で照合する。

---

## 2. 相互整合 (1 つでも破れば `[s8b-terminal-evidence]` で拒否、`observed` へ落とさない)

- `probe_after is None` ⇔ `probe_before.competing` ⇔ (`failure` null ∧ `launch_failures_count == 0`
  ∧ `throughputs` 空 ∧ `rep_observations_sha256` が空列の digest ∧ `rep_integrity_failures` null
  ∧ `exec_failures == 0`)
- opened (`failure` null ∧ `probe_after` 非 null) ⇒ sink 長 = `reps_expected` ∧
  `rep_integrity_failures` は int ∧ `exec_failures` は sink 由来
- `failure` 非 null ⇒ 計測なし ∧ `exec_failures == reps_expected` (unavailable projection と明記)
- `launch_failures_count > 0` ∧ `exec_failures == 0` は矛盾 → 拒否
- opened のとき `len(throughputs) + nonfinite_count + exec_failures == reps_expected`

---

## 3. `exec_failures` の射程 [裁定 2]

**契約 v2 の定義は誤りだった。`exec_failures` と `rep_integrity_failures` は別の量である。**

- `exec_failures` = runner が rep の `open()` で捕捉した**実行例外**の数
- `rep_integrity_failures` = 戻り値 / counter / schema / 欠損を独立に検査した**証跡不完備**の数

同じ rep で両方が立つことがある。契約 v2 の「非 zero の戻り値または起動失敗をすべて
`exec_failures` と数える」は誤り。「契約を現行の notes regex 算出に合わせる」案は**却下**する —
それでは証拠が「campaign が自然文から何件と数えたか」しか証明せず、自然文を信頼経路に残す。

**C1b の射程はここで切る。**

- C1b の証拠は `exec_failures` を `campaign_record.exec_failures` との**等値でのみ束縛する**。
- **「この値が各 rep の実行成否を証明する」とは主張しない。** 主張できないことを主張しない (規律 3)。
- runner の構造化 `execution_failure`、campaign の算出変更、rep observation の 6 key → 7 key 化と
  それに伴う凍結 gate の pin 閉包は **C2 が持つ。C1b へ混ぜない。**

---

## 4. 再導出 (E1) — campaign の実 semantics が正本 [訂正 D / probe P-6]

契約 v2 は「campaign `_run_session` と同順」と書いたが実際には一致していなかった。
v3 は `s8b_floor_campaign.py` の `_run_session` を**そのまま**正本にする。

| 枝 | 条件 | E2 の語 | campaign の凍結語 |
|---|---|---|---|
| 1 | `probe_before.competing ∨ probe_after.competing` | `measurement_environment_conflict` | `competing_process` |
| 2 | `failure` 非 null **または** `exec_failures >= reps_expected` | `measurement_execution_unavailable` | `launch_failure` |
| 3 | `0 < exec_failures < reps_expected` **かつ** assessed reason が null | `measurement_execution_unavailable` | `launch_failure` |
| 4 | `rep_integrity_failures > 0` **かつ** assessed reason が partial | `measurement_sample_incomplete` | `nonfinite_or_partial_output` |
| 5 | assessed reason が `nonfinite_or_partial_output` | `measurement_sample_incomplete` | `nonfinite_or_partial_output` |
| 6 | assessed reason が `performance_anomaly` | `measurement_dispersion_exceeded` | `performance_anomaly` |
| 7 | それ以外 | (なし) | null。状態 `observed`、primary = `assess_session.median` |

枝 2 と枝 3 が同じ E2 語を返すのは意図どおりである。full / partial の排他 fixture を使う限り
両者を分離して変異で殺し分けられる。

**E2 の 4 語** = `measurement_environment_conflict` / `measurement_execution_unavailable` /
`measurement_sample_incomplete` / `measurement_dispersion_exceeded`
(`S8B_V2_RETRYABLE_FAILURE_REASONS`。**v1 は空のまま**)。

状態語は「理由あり = `retryable-failure`」「理由なし = `observed`」。
**E1 は `terminal-failure` と `not-consumed` を出さない。**

`campaign_record.excluded_reason` が再導出の campaign 語と一致しなければ拒否する。

---

## 5. 観測後の理由は別 field に載せる [裁定 1 / probe P-1]

**これが v2 が実体化できなかった箇所の訂正であり、契約 v3 の中核である。**

`attempt_registry_core.py` の等値検査 (`require_terminal_reason_equals_classification`) と
null matrix を同時に満たす `failure_reason` は、v2 の書き方では存在しなかった。launcher の
分類語彙 (`competing_process` / `launch_failure`) と E2 の 4 語が互いに素で、しかも
`measurement_sample_incomplete` と `measurement_dispersion_exceeded` は `open()` の後にしか
判明しないのに分類は `open()` の前に起きるためである。

### 5.1 決定

- **`failure_reason` は観測前 classification の exact echo のままにする。** core の等値検査を
  1 行も変えない。
- **E2 の 4 語は v2 専用の新 field `measurement_retry_reason` に載せる。**
- `_assert_null_matrix` へ `reason_field` を渡し、`retryable_reasons` の照合先を profile が選ぶ。
- `DomainProfile` へ `retryable_reason_field: str = "failure_reason"` (keyword-only、既定は現行) を
  足し、**v2 profile だけ** `"measurement_retry_reason"` を指す。

**A 案 (validated capability があるときだけ等値検査を飛ばす policy flag) は採らない。**
既存の正しさ検査へ条件付きの迂回路を新設する形であり、capability を持たない呼び手が
迂回路へ到達できない B 案のほうが規律 2 に対して厳密に強い。

### 5.2 通る形 (probe P-1 で実測、5/5)

| 場合 | 分類理由 | `failure_reason` | `measurement_retry_reason` | 状態 |
|---|---|---|---|---|
| 観測前・競合 | `competing_process` | `competing_process` | `measurement_environment_conflict` | `retryable-failure` |
| 観測前・起動失敗 | `launch_failure` | `launch_failure` | `measurement_execution_unavailable` | `retryable-failure` |
| 観測後・標本不足 | null | null | `measurement_sample_incomplete` | `retryable-failure` |
| 観測後・分散超過 | null | null | `measurement_dispersion_exceeded` | `retryable-failure` |
| 観測成功 | null | null | null | `observed` |

### 5.3 閉じる穴 (probe P-1 の N1 / N4 で実測)

現行の `_assert_null_matrix` は `observed` 枝と `not-consumed` 枝で新 field を一切見ない。
**このままだと観測に成功した行や未消費の行へ「測り直しの理由」を載せられる。**
契約 v3 は次の 2 条項を足す。

- `observed` ⇒ `measurement_retry_reason is None`
- `not-consumed` ⇒ `measurement_retry_reason is None`

拒否は署名で書く。`[attempt-null-matrix] ... observed null matrix differs` /
`... not-consumed null matrix differs` の既存署名を使い、**通る正例は 5.2 の
「観測成功」行と「観測前・競合」行**とする。

### 5.4 v2 terminal 行の key は 2 つ増える

`terminal_evidence_sha256` と `measurement_retry_reason`。**v1 の key 集合と受理集合は
1 bit も変わらない。**

現行の `_S8B_V2_EVENT_KEYS` は v1 の全 event へ `measurement_ordinal` を一律に足す内包表記なので、
**terminal だけに 2 key を足すには event 別の分岐が要る** (probe P-1 で実測)。
`record_attempt_terminal` は `terminal_keys` に含まれるときだけ行へ載せる形にする —
これは既存の `pre_observation_failure_reason_echo` と同じ seam である。

---

## 6. 封印の発行経路と信頼境界 [訂正 B / 訂正 G / 裁定 3 / probe P-5]

### 6.1 発行は 2 段にする

- `seal_terminal_evidence(reservation, opened, terminal)` は**未完成の
  `SealedTerminalEvidenceDraft`** を返す。公開 signature は契約 v2 のまま変えない。
- **adapter が exact な `CapturedObservation` から 3 digest を補って初めて
  `ValidatedTerminalEvidence` を発行する。** launcher だけでは validated capability を得られない。
- capability を渡せる入口は **1 本に限定**する。core の全 load API へ keyword を伝播しない。
- launcher は core の capability を受け取らない。

### 6.2 test seam を塞ぐ

`_launch_floor_attempt_for_test()` は production と同じ本体を呼び `registry` を注入できる。
**adapter を経由させるだけでは塞がらない。** validated capability の構築子は adapter module の
私有名前空間に閉じ、core は**厳密型で受理する**。現行の handle 機構 (`_new_handle` /
`_require_handle` が厳密型・私有 token・weakref 同一性・state fingerprint・attempt key の
5 点を照合する) が前例で、**interface を真似ただけの偽 registry は validated capability を
作れない**形はこれで作れる。

### 6.3 capability の権威は canonical bytes [訂正 G]

capability の唯一の実データを **immutable な canonical bytes** にする。`document` と `projection`
は毎回その bytes から再生成し、表には bytes digest と identity fingerprint だけを保存する。
**発行台帳への membership を権威にしない** — 直接 insert・private 発行子の直呼び・
`__reduce_ex__` がいずれも通ることをレンズ A が実測した。

### 6.4 脅威に含める / 含めない (明記する)

**含める:** 外部 CCBench と生成 variant が返す悪意ある bytes・戻り値・出力、通常の Python 操作に
よる capability 内容の書き換え、誤った production caller。

**含めない:** 任意の同一 process module 改変、private issuer の意図的な直接呼出し、reflection 操作、
同一 Unix uid による registry と validator の同時改変。

**別 process の issuer は作らない。** 同一 uid・同一 repository・同一の検証コードを使う限り
独立性は増えず、IPC と crash 状態だけが増える。これは D387 が既に述べている限界と同じであり、
**主張せず明記する** (規律 7 の書き方)。

---

## 7. crash 後の権威

1. 台帳行 + receipts dir の bytes。
2. 行の digest が指す no-follow regular file を root lock 下で読み、filename / bytes digest /
   strict JSON / exact keys / canonical bytes / `attempt_binding` を検査。
3. file から再導出した状態 / 理由 / 主値 / 3 digest / 分類理由が行と一致した場合だけ受理。

row あり file なし・digest 不一致・内容不一致は拒否。file あり row なしは許容。

---

## 8. 採らないもの (自発的拡張) [訂正 H]

契約が要求していないので採らない。

- durable claim の新 schema (claim v4) — 既存 claim に `mode` がある
- `_AttemptState` への `mode` 追加
- core 公開 API 8 surface への capability 伝播

---

## 9. 射程の限界 (主張しないこと)

- **`launch_floor_attempt()` の production 呼び手は 0 件である** (probe P-7 で再実測)。
  本単位の gate 入力は fake 由来の値域しか実測できない。E1 の枝は campaign の実 semantics へ
  静的に照合するに留め、**「実環境の値域」を主張しない。** 実値域は C2 が供給する。
- `exec_failures` は等値束縛だけで、rep ごとの実行成否は証明しない (3 節)。
- 同一 process 内の module 改変に対する防壁は主張しない (6.4)。
- `attempt_registry_core.py` は `test_reflux_formal_consumer.py` の AST 走査下にあり、
  `aborted=False` の keyword 呼び出しと `OriginSealed(False, ...)` を書いてはならない (probe P-7)。
