# [T-1851] terminal 証拠の契約 v3.1 (確定版・正本)

**この文書が契約の正本である。** 同 dir の `contract-v3.md` は本文書が supersede した
(規律 7 の追記訂正。v3 を遡って削除・改変しない)。

系譜は次のとおり。

- 契約 v2 = `output/insights/2026-09-07_t1851-unit-c-launcher-raw-facts/s4-adjudication.md` 3 節
- 契約 v2 の欠陥 7 件 + 偽造 2 件 = `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/`
- 未裁定 4 件の決着 = 同 dir の `rulings-resolved.md`
- 契約 v3 = 本 dir の `contract-v3.md` (段 1。consumer probe つき)
- **契約 v3.1 = 本文書** (段 4。段 3 の敵対レンズ 2 本が出した blocker を閉じた)

**確定の条件:** 各条項には、それを束縛する consumer へ実際に通した probe 番号、または
段 3 の所見番号と親の裏取りを付ける。根拠のない条項は契約に入れない。

- C1b が実体化する。C2 が供給する。D2 が再検証する。
- **land しない (D1341)。** 6 単位が揃うまで branch 上の checkpoint に留める。

---

## 0.1 v3 からの変更 (6 件)

| # | 節 | 変更 | 根拠 |
|---|---|---|---|
| 1 | 1.5 | identity 群を「権威がある」「権威が無い」の 2 群に分け、後者は digest 束縛だけにして**権威だと主張しない** | A-01 (親が durable claim の現物で裏取り) |
| 2 | 4 | E1 の入力値域は **launcher の捕捉集合**であって campaign の捕捉集合ではないと明記し、`OSError` の扱いを固定 | A-02 (親が両側の except 節で裏取り) |
| 3 | 5 | probe P-1 の射程を書き直し、5.3 の `not-consumed` 正例を D1522 の下層直呼びで作る。両枝が同じ field を読むことを固定する条項を追加 | A-04 / A-05 / B-11 |
| 4 | 6.1 | draft 時点で欠ける 3 digest の表現と、adapter が補う private ABI の形を規定 | B-03 |
| 5 | 7 | row と file の全件等値へ `finished_at` を追加 | A-03 |
| 6 | 9 | semantic な perf inventory が pin 閉包に残ることを明記 | B-07 (親が現物で裏取り) |

---

## 0. 何を守る契約か (裁定 0)

守る対象は **「試行 proof chain に虚偽の terminal 事実が入ること」だけ**である。床値の数値は
既存の verifier と journal からの再計算が守っており、本契約はそこを守らない。

塞ぐ穴は 1 つである。正当な予約・分類・観測開始までを通常経路で作り、terminal builder だけが
任意の出力 bytes・状態・digest・主値・測り直し理由を返すと、台帳 core は形と相互整合しか見ないため
その行が hash chain に載る。`capture_attempt_registry_prefix()` がその chain head を result v5 に載せ、
live verifier / holdout freeze / ratified freeze が同じ prefix を受理する。

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

### 1.1 再導出面 (平文) と束縛面 (digest) を分ける [probe P-2]

契約 v2 は `probe_before` / `probe_after` / `campaign_record` を exact に載せると書いた。
これは **guarded writer が必ず拒否する**。証拠文書は `_write_staging()` を通り、
`assert_holdout_safe_bytes()` が holdout の三軸 conjunction を走査するためである。

**平文に載せてよいのは、E1 の 6 枝と 2 節の相互整合が実際に読む値だけである。**
測定した境界は「三軸のうち 2 軸までは通り、3 軸そろうと落ちる」で、`holdout_id` と `cell_id` は
単独では汚染しないので平文で残す。

| 面 | 載せるもの |
|---|---|
| 平文 (再導出面) | `schema_version`、`attempt_binding`、`mode`、`expected_use_perf`、`finished_at`、`session_cv_max`、`reps_expected`、`throughputs` (有限のみ)、`nonfinite_count`、`exec_failures`、`rep_integrity_failures`、`launch_failures_count`、`failure` の `stage` と非 null 性、probe 組の `competing` と rc・stdout・stderr の**空か否か**、`campaign_record` の権威つき identity と計測 field |
| 束縛面 (digest) | `campaign_record_sha256`、`workload_sha256`、`run_cmd_sha256`、`notes_sha256`、`rep_observations_sha256`、`probe_before_sha256`、`probe_after_sha256`、`failure_message_sha256`、`launch_failures_sha256`、`perf_preflight_receipt_sha256`、`raw_output_sha256`、`report_sha256`、`observation_sha256`、**`unauthored_identity_sha256`** (1.5) |

**最終 canonical bytes は既存の holdout-safe gate を必ず通す。専用 bypass は作らない。**

### 1.2 平文 field の出所と束縛

D1113 (呼び手は証拠の値を選べない) を全 field へ適用する。v3 の表をそのまま引き継ぐ。
変更は 1.5 の identity 群だけである。

| field | 出所 | 束縛 |
|---|---|---|
| `schema_version` | launcher 定数 | literal |
| `attempt_binding` | reservation + handle state | exact object。3 digest の綴りは 1.3 |
| `protocol` | reservation (normalized 全体) | `canonical_protocol_sha256(protocol) == binding.protocol_sha256` を launcher で副作用前、adapter で再検査 |
| `mode` | durable claim | claim の `mode` と等値 |
| `perf_preflight_receipt_sha256` + `expected_use_perf` | reservation | `expected_use_perf == use_perf_from_receipt(receipt)`。official + receipt 非 null + True は拒否。capture kwargs `use_perf` (省略時 True) と等値。**判定の導出箇所は launcher の既存 gate 1 本に限る** (9 節) |
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
| `finished_at` | launcher の注入 clock (`classified_at` と同じ callable) | text。**7 節で row と全件等値** |

### 1.3 `attempt_binding` の 3 digest [probe P-5 / B-02]

`_AttemptState` (`s8b_attempt_registry.py:182-184`) が持つのは
`classification_receipt_sha256` / `classification_event_sha256` / **`observation_event_sha256`**。
契約 v2 が書いた `observation_start_event_sha256` は誤りで、**契約は現物の綴りを採る。**

**ただし terminal 行側の field 名は `observation_start_event_sha256` である。**
両者は別の名前空間であり、同名化してはならない。証拠の `attempt_binding.observation_event_sha256` と
行の `observation_start_event_sha256` を**明示的に対応づけて等値検査する**。

launcher の 3 型はこの 3 digest を持たない。したがって発行は 2 段になる (6.1)。

### 1.4 非有限値の表現 [probe P-4]

- **`throughputs` は有限値だけの列**にする。非有限の本数は `nonfinite_count` が持つ。
- 不変条件は `len(throughputs) + nonfinite_count + exec_failures == reps_expected`。
- E1 の `assess_session` へは **有限のみの列と、元の `reps_expected`** を渡す。
- **落とした本数の分だけ `reps` を減らしてはならない。** 減らすと `required_reason` が消えて
  欠測が健全な session に見える (probe P-4 で実測)。

### 1.5 `campaign_record` は exact 30 key。identity は権威の有無で 2 群に分ける [probe P-3 / **A-01**]

exact 集合の正本は `s8b_ratified_freeze._JOURNAL_KEYS["session"]` で、**exact 30 key**。

```
attempt_id binary_sha256_at_measure cell_id configuration_id duration_s event
excluded_reason exclusion_class exec_failures holdout_id kind notes probe_after
probe_before records rep_integrity_failures rep_observations reps_expected retry
retry_ordinal round run_cmd seq session_cv session_median threads throughputs
trigger valid workload
```

**v3 の「identity 13 field を reservation と全件等値」は誤りだった。** reservation は呼び手が
組み立てる公開 dataclass であり、そこへ写した値を権威にすると「呼び手が証拠の値を選べない」
(D1113) を満たさない。親が durable claim の現物を読み、権威の所在を測った。

#### (a) 権威のある identity — **再導出して等値束縛する**

| field | 権威の所在 |
|---|---|
| `cell_id` | durable measurement-generation claim (`s8b_holdout_admission.py:1719`) |
| `records` / `threads` / `workload` | 同 claim (`:1720-1722`)。**`mode` だけでなくこの 3 つも claim から再照合する** |
| `attempt_id` | 同 claim の `attempt_ids` に含まれること |
| `configuration_id` / `holdout_id` | v2 slot の `configuration_id` / `freeze_holdout_key`。`schedule_row_sha256` で凍結 schedule 行に束縛 |
| `retry_ordinal` | v2 slot の `attempt_ordinal` と対応づけて等値 |
| `campaign_run_id` / `run_relpath` / `manifest_sha256` / `mode` | 同 claim |

#### (b) 権威の無い identity — **digest でのみ束縛し、権威だと主張しない**

`event` / `kind` / `seq` / `round` / `trigger` / `retry` には durable な権威が存在しない。
campaign の帳簿上の値であり、C1b が参照できる凍結物のどれにも入っていない。

- これらは平文へ載せず、**`unauthored_identity_sha256`** 1 本にまとめて digest 束縛する。
- 証拠は「この attempt の帳簿上の位置がこの値だった」と**主張しない。**
  主張できないことを主張しない (規律 3)。`exec_failures` の射程 (3 節) と同じ切り方である。
- **これらの値を E1 の判定入力に使ってはならない。**

#### (c) 計測群 — 平文

`throughputs` `reps_expected` `exec_failures` `rep_integrity_failures` `session_median`
`session_cv` `duration_s` `valid` `excluded_reason` `exclusion_class` `binary_sha256_at_measure`。
`excluded_reason` / `session_median` / `valid` は再導出と全件等値で照合する。

#### (d) 束縛群 — digest のみ

`notes` `run_cmd` `probe_before` `probe_after` `rep_observations` `workload`
(`workload` は (a) の claim 照合を平文外で行い、証拠には digest だけを載せる)。

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

同じ rep で両方が立つことがある。「非 zero の戻り値または起動失敗をすべて `exec_failures` と数える」は
誤り。「契約を現行の notes regex 算出に合わせる」案は却下する — 自然文を信頼経路に残すためである。

**C1b の射程はここで切る。**

- 証拠は `exec_failures` を `campaign_record.exec_failures` との**等値でのみ束縛する**。
- **「この値が各 rep の実行成否を証明する」とは主張しない** (規律 3)。
- runner の構造化 `execution_failure`、campaign の算出変更、rep observation の 6 key → 7 key 化と
  それに伴う凍結 gate の pin 閉包は **C2 が持つ。C1b へ混ぜない。**

---

## 4. 再導出 (E1) [probe P-6 / **A-02**]

### 4.1 枝の順序は campaign の実 semantics に合わせる

`s8b_floor_campaign.py` の `_run_session` を正本にする。

| 枝 | 条件 | E2 の語 | campaign の凍結語 |
|---|---|---|---|
| 1 | `probe_before.competing ∨ probe_after.competing` | `measurement_environment_conflict` | `competing_process` |
| 2 | `failure` 非 null **または** `exec_failures >= reps_expected` | `measurement_execution_unavailable` | `launch_failure` |
| 3 | `0 < exec_failures < reps_expected` **かつ** assessed reason が null | `measurement_execution_unavailable` | `launch_failure` |
| 4 | `rep_integrity_failures > 0` **かつ** assessed reason が partial | `measurement_sample_incomplete` | `nonfinite_or_partial_output` |
| 5 | assessed reason が `nonfinite_or_partial_output` | `measurement_sample_incomplete` | `nonfinite_or_partial_output` |
| 6 | assessed reason が `performance_anomaly` | `measurement_dispersion_exceeded` | `performance_anomaly` |
| 7 | それ以外 | (なし) | null。状態 `observed`、primary = `assess_session.median` |

枝 2 と枝 3 が同じ E2 語を返すのは意図どおりである。

### 4.2 **入力の値域は campaign の捕捉集合と同じではない (A-02)**

契約 v3 は「campaign の実 semantics が正本」と書いたが、それだけでは E1 の受理集合を束縛できない。
親が両側の except 節を読んで測った。

- launcher: `except (RuntimeError, subprocess.TimeoutExpired, OSError)`
  (`s8b_floor_attempt_launcher.py:777`)
- campaign: `except (RuntimeError, subprocess.TimeoutExpired)` (`s8b_floor_campaign.py:6264`)

**`OSError` は launcher では `failure.stage="capture"` の terminal になるが、campaign では
session 行そのものが生まれない。** したがって「campaign と同順だから受理集合も同じ」は成立しない。

**契約 v3.1 の決定:**

- E1 の**枝の順序**は campaign を正本にする (4.1)。
- E1 の**入力値域**は launcher の捕捉集合であると明記する。証拠は
  `failure.exception_type` を平文に載せ、`OSError` 由来の terminal を
  `measurement_execution_unavailable` として受理する。
- **ただし「campaign が同じ入力で同じ語を出す」とは主張しない。** campaign 側に対応する
  session 行が存在しない値域があることを射程として書く (9 節)。
- 実装は `failure.exception_type` が launcher の捕捉集合 (`RuntimeError` /
  `subprocess.TimeoutExpired` / `OSError` の 3 語) の exact member であることを検査する。
  集合外の型名は拒否する。

### 4.3 E2 の語と状態語

**E2 の 4 語** = `measurement_environment_conflict` / `measurement_execution_unavailable` /
`measurement_sample_incomplete` / `measurement_dispersion_exceeded`
(`S8B_V2_RETRYABLE_FAILURE_REASONS`。**v1 は空のまま**)。

状態語は「理由あり = `retryable-failure`」「理由なし = `observed`」。
**E1 は `terminal-failure` と `not-consumed` を出さない。**

`campaign_record.excluded_reason` が再導出の campaign 語と一致しなければ拒否する。

---

## 5. 観測後の理由は別 field に載せる [裁定 1 / probe P-1 / **A-04 / A-05 / B-11**]

### 5.1 決定

- **`failure_reason` は観測前 classification の exact echo のままにする。** core の等値検査を
  1 行も変えない。
- **E2 の 4 語は v2 専用の新 field `measurement_retry_reason` に載せる。**
- `_assert_null_matrix` へ `retryable_reason_field` を渡し、`retryable_reasons` の照合先を
  profile が選ぶ。
- `DomainProfile` へ `retryable_reason_field: str = "failure_reason"` (keyword-only、既定は現行) を
  足し、**v2 profile だけ** `"measurement_retry_reason"` を指す。

**A 案 (validated capability があるときだけ等値検査を飛ばす policy flag) は採らない。**
既存の正しさ検査へ条件付きの迂回路を新設する形であり、capability を持たない呼び手が
迂回路へ到達できない B 案のほうが規律 2 に対して厳密に強い。

#### 5.1.1 **両枝が同じ field を読むこと (B-11)**

`retryable_reason_field` は `retryable-failure` 枝と `terminal-failure` 枝の**両方**に適用する。

これは恒真になりやすい。**`terminal-failure` 枝だけ `failure_reason` 固定のまま残す変異は、
通常経路では生存する** — v1 は既定が同じで差が出ず、canonical v2 は E1 が `terminal-failure` を
出さないので後段の証拠 validator が先に拒否して差が隠れるためである。

**したがってこの条項の検査は D1522 に従い、上流が拒否する形でも下層を直接呼ぶ test で置く。**
`_assert_null_matrix` を v2 profile の `retryable_reason_field` つきで直接呼び、
`terminal-failure` 行に対して照合先が切り替わっていることを単独で確かめる。

### 5.2 通る形 (probe P-1 で実測、5/5)

| 場合 | 分類理由 | `failure_reason` | `measurement_retry_reason` | 状態 |
|---|---|---|---|---|
| 観測前・競合 | `competing_process` | `competing_process` | `measurement_environment_conflict` | `retryable-failure` |
| 観測前・起動失敗 | `launch_failure` | `launch_failure` | `measurement_execution_unavailable` | `retryable-failure` |
| 観測後・標本不足 | null | null | `measurement_sample_incomplete` | `retryable-failure` |
| 観測後・分散超過 | null | null | `measurement_dispersion_exceeded` | `retryable-failure` |
| 観測成功 | null | null | null | `observed` |

#### 5.2.1 **probe P-1 の射程 (A-04)**

probe は `dataclasses.replace(v2, terminal_row_validator=None)` を使い、
**v2 の無条件拒否 hook `_reject_unsealed_s8b_v2_terminal` を無効化して測った。**
その hook は C1b が封印証拠 validator へ置き換える対象である。

**probe が示したのは「hook を置き換えたあと、その手前にある core の等値検査・null matrix・
exact key 検査を 5 形が通るか」までである。** 前 wave が「1 行も書けない」と測ったのは
まさにこの手前の 2 検査なので、probe はその問いに答えている。

**probe は leaf・adapter・durable evidence 経路を測っていない。**
「5 形が端から端まで通る」とは主張しない。実例として、`observed` 行へ任意の
`primary_value=999` を入れても現行 null matrix は受理する — 証拠 validator が拒否する形であり、
core を通ったことは証拠 validator を通ったことを含意しない。

### 5.3 閉じる穴 [probe P-1 の N1 / N4、**A-05**]

現行の `_assert_null_matrix` は `observed` 枝と `not-consumed` 枝で新 field を一切見ない。
観測に成功した行や未消費の行へ「測り直しの理由」を載せられる。契約は次の 2 条項を足す。

- `observed` ⇒ `measurement_retry_reason is None`
- `not-consumed` ⇒ `measurement_retry_reason is None`

**正例の置き場所が枝ごとに違う。ここを間違えると恒真な拒否になる。**

| 条項 | 拒否の署名 | 正例 (通る形) |
|---|---|---|
| `observed` | `[attempt-null-matrix] ... observed null matrix differs` | 5.2 の「観測成功」行。**同じ枝の正例がある** |
| `not-consumed` | `[attempt-null-matrix] ... not-consumed null matrix differs` | **sealed 経路に同じ枝の正例は存在しない。** E1 は `not-consumed` を出さず、証拠 validator は E1 projection と行の状態一致を要求する |

`not-consumed` の正例は **D1522 に従い下層を直接呼んで作る。**
`_assert_null_matrix` へ「`measurement_retry_reason` が null の `not-consumed` 行」を直接渡して
受理させ、非 null の同じ行が拒否されることを対で置く。**上流の sealed 経路を正例に使わない。**
これをしないと、`not-consumed` 枝を常に拒否する誤実装が緑のまま通る。

### 5.4 v2 terminal 行の key は 2 つ増える

`terminal_evidence_sha256` と `measurement_retry_reason`。**v1 の key 集合と受理集合は
1 bit も変わらない。**

現行の `_S8B_V2_EVENT_KEYS` (`s8b_attempt_profile.py:490`) は v1 の全 event へ
`measurement_ordinal` を一律に足す内包表記なので、**terminal だけに 2 key を足すには
event 別の分岐が要る** (probe P-1 で実測)。
`record_attempt_terminal` は `terminal_keys` に含まれるときだけ行へ載せる形にする —
これは既存の `pre_observation_failure_reason_echo` と同じ seam である。
**v1 へ非 null の新 field を渡した場合は拒否する。黙って捨ててはならない。**

---

## 6. 封印の発行経路と信頼境界 [probe P-5 / **B-03**]

### 6.1 発行は 2 段にする。**draft の形を規定する (B-03)**

- `seal_terminal_evidence(reservation, opened, terminal)` は**未完成の
  `SealedTerminalEvidenceDraft`** を返す。公開 signature は契約 v2 のまま変えない。
- **adapter が exact な `CapturedObservation` から 3 digest を補って初めて
  `ValidatedTerminalEvidence` を発行する。**

**時系列の問題を契約で閉じる。** `seal_terminal_evidence()` が呼ばれる時点では
observation-start がまだ発行されておらず、`observation_event_sha256` は存在しない。
また `classification_receipt_sha256` と `classification_event_sha256` も
`_AttemptState` にしかない。したがって draft の `attempt_binding` は 12 key のうち
**3 key が未確定**である。

**決定:**

- draft の `attempt_binding` は **9 key の exact 集合**とする。3 digest の key は
  **存在しない** (null を置くのではなく key ごと欠落させる)。null を許すと
  「null のまま validated へ昇格した」形と区別できない。
- `ValidatedTerminalEvidence` の `attempt_binding` は **12 key の exact 集合**とする。
- adapter の private 昇格関数の形を契約で固定する。

```python
def _promote_draft_to_validated(
    draft: SealedTerminalEvidenceDraft,
    *,
    classification_receipt_sha256: str,
    classification_event_sha256: str,
    observation_event_sha256: str,
    issuer_token: object,
) -> ValidatedTerminalEvidence: ...
```

- 昇格は **draft の canonical bytes を復号して 3 key を足し、canonical bytes を作り直す**。
  draft の bytes をそのまま流用してはならない。digest は作り直した bytes から取る。
- `issuer_token` は adapter module 私有の object であり、外部から到達できない。
- **leaf は昇格関数を持たない。** leaf が公開する `require_sealed_terminal_evidence(value)` は
  既発行 capability の**厳密検査**であって、draft を validated へ昇格させる関数ではない。

### 6.2 test seam を塞ぐ

`_launch_floor_attempt_for_test()` は production と同じ本体を呼び `registry` を注入できる。
**adapter を経由させるだけでは塞がらない。** validated capability の構築子は adapter module の
私有名前空間に閉じ、core は**厳密型で受理する**。現行の handle 機構 (`_new_handle` /
`_require_handle` が厳密型・私有 token・weakref 同一性・state fingerprint・attempt key の
5 点を照合する) が前例で、**interface を真似ただけの偽 registry は validated capability を
作れない**形はこれで作れる (レンズ A の A-08 が独立に確認)。

### 6.3 capability の権威は canonical bytes

capability の唯一の実データを **immutable な canonical bytes** にする。`document` と `projection`
は毎回その bytes から再生成し、表には bytes digest と identity fingerprint だけを保存する。
**発行台帳への membership を権威にしない。**

### 6.4 脅威に含める / 含めない (明記する)

**含める:** 外部 CCBench と生成 variant が返す悪意ある bytes・戻り値・出力、通常の Python 操作に
よる capability 内容の書き換え、**誤った production caller**。

**含めない:** 任意の同一 process module 改変、private issuer の意図的な直接呼出し、reflection 操作、
同一 Unix uid による registry と validator の同時改変。

**別 process の issuer は作らない。** 同一 uid・同一 repository・同一の検証コードを使う限り
独立性は増えず、IPC と crash 状態だけが増える。D387 が述べる限界と同じであり、
**主張せず明記する** (規律 7 の書き方)。

なお 1.5 の (a) は「誤った production caller」を脅威に含めることの直接の帰結である。
呼び手が組み立てた reservation を権威にすると、この脅威に対して無防備になる。

---

## 7. crash 後の権威 [**A-03**]

1. 台帳行 + receipts dir の bytes。
2. 行の digest が指す no-follow regular file を root lock 下で読み、filename / bytes digest /
   strict JSON / exact keys / canonical bytes / `attempt_binding` を検査。
3. file から再導出した値が行と一致した場合だけ受理する。**全件等値の対象は次のとおり。**

| 行の field | 証拠側 |
|---|---|
| `terminal_status` | projection の状態 |
| `failure_reason` | projection の分類 echo |
| `measurement_retry_reason` | projection の E2 語 |
| `primary_value` | projection の主値 |
| `raw_output_sha256` | 同名 |
| `report_sha256` | 同名 |
| `observation_sha256` | 同名 |
| `classification_receipt_sha256` | `attempt_binding` の同名 |
| `observation_start_event_sha256` | `attempt_binding.observation_event_sha256` (1.3 の対応づけ) |
| **`finished_at`** | **同名 (A-03 で追加)** |
| `terminal_evidence_sha256` | file bytes の digest |

`finished_at` が抜けていると、file を据え置いたまま行の時刻だけ書き換えて event hash を
再計算する改竄を検出できない。core は `finished_at` が text であることしか見ない
(`attempt_registry_core.py:1039`)。

row あり file なし・digest 不一致・内容不一致は拒否。file あり row なしは許容。

---

## 8. 採らないもの (自発的拡張)

- durable claim の新 schema (claim v4) — 既存 claim に `mode` がある
- `_AttemptState` への `mode` 追加
- core 公開 API 8 surface への capability 伝播

---

## 9. 射程の限界 (主張しないこと)

- **`launch_floor_attempt()` の production 呼び手は 0 件である。** 本単位の gate 入力は
  fake 由来の値域しか実測できない。**「実環境の値域」を主張しない。** 実値域は C2 が供給する。
  (test caller は public 2 件、test seam 13 件、共通本体 2 件 — B-09)
- `exec_failures` は等値束縛だけで、rep ごとの実行成否は証明しない (3 節)。
- **`event` / `kind` / `seq` / `round` / `trigger` / `retry` は権威を持たない。**
  証拠はこれらを digest でのみ束縛し、帳簿上の位置が正しいとは主張しない (1.5 (b))。
- **E1 の入力値域は launcher の捕捉集合であり、campaign の捕捉集合ではない。**
  `OSError` 由来の terminal に対応する campaign session 行は存在しない (4.2)。
- 同一 process 内の module 改変に対する防壁は主張しない (6.4)。
- **pin 閉包は identifier 検索だけでは閉じない (B-07)。**
  `test_official_perf_closure.py:44` の `_REVIEWED_PERF_FILES` は exact frozenset で、
  `:531` の `_production_perf_files()` が production を AST 走査し `:903` が集合等値を assert する。
  **新 leaf に perf 述語の分岐を置くとこの inventory が落ちる。**
  実装は `expected_use_perf` の導出を launcher の既存 gate
  (`s8b_floor_attempt_launcher.py:565-588`) 1 本に保ち、leaf には perf 述語の新しい直接 call を
  置かない。generic helper の背後へ隠して test だけ緑にする逃げ方は取らない。
- `attempt_registry_core.py` は `test_reflux_formal_consumer.py` の AST 走査下にあり、
  `aborted=False` の keyword 呼び出しと `OriginSealed(False, ...)` を書いてはならない。
