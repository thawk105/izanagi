# [T-1851] 段 4 裁定 — 単位 C: terminal 証拠の契約 v2 を固定し、本 wave の実装は C1a (起動層の raw facts 面) に絞る

日付: 2026-09-05 21:10 JST。branch `worktree-dev-wave-t1851-unit-a`、tip `04f06d032`。
入力: `s1-brief.md`、`artifacts/t1851-unit-c/s2-plan.md` (488 行)、`s3-lens-a.md` (blocker 7 / must-fix 4 / nit 2)、`s3-lens-b.md` (blocker 6 / must-fix 9 / nit 1)。
裁定 inbox の再走査: decisions.md は D1643 まで、terminal 証拠・E1 / E2・T-1851 に触れる新規裁定なし (wave 開始後の main 進行 0 commit)。

## 1. 結論

1. **terminal 証拠の契約は v2 (下の 3 節) で固定する。** plan の 19 field に、両レンズが独立に要求した attempt 束縛と cross-field 不変条件を足す。
   これは docs (本裁定 + decisions fragment) として固定し、コードでの実体化は C1b が行う。
2. **本 wave の実装は C1a に絞る。** 実装子 1 本 (launcher + launcher test)。C1b (証拠 module、封印 API、E1 / E2、durable artifact、core / profile) は
   次 wave。(P5) は却下し、plan の C1a / C1b 分割を、レンズ B 所見 4 の「C1a では v2 を副作用前に専用署名で拒否する」条件付きで採る。
3. **D1530 は C1 では達成しない** (レンズ A 所見 1、real)。C1a / C1b は unlanded checkpoint であり、land 単位は C2 (campaign の呼び手) と
   D2 まで含む 1 変更単位のまま (D1341)。「効いている」「D1530 達成」とは書かない。
4. ユーザー裁定を要する択一 3 件は 6 節へ返す。いずれも本 wave の C1a を止めない (C1a は択一のどちらでも不変)。

## 2. 所見の裁定 (real / refuted、採否、scope)

| # | 所見 | 判定 | 採否・scope |
|---|---|---|---|
| A1 | C1 単独では D1530 の呼び手を繋がない | real | 採用。記録の文言を「checkpoint、land 単位は C2 まで」に固定。実装なし |
| A2 / B2 | `mode` / `perf_preflight_receipt` / `ClassificationAuthority` が呼び手選択 | real | 採用。**C1a:** 分類 authority を launcher 定数 + policy bytes の digest から導出し public API の引数を除く。`mode` は exact literal 検査、receipt は形の検査と `expected_use_perf` の機械導出 + capture kwargs `use_perf` との等値。**C1b:** `mode` は adapter が durable claim の `mode` と照合。**C2 + D2:** receipt の manifest canonical bytes への束縛は campaign が渡し verify が再読 (6 節 4) |
| A3 / B10 | seal が文書 sealer では偽造可能 | real | 採用 (C1b)。launcher 私有の capture / probe state を消費する issued handle。issuer table に reservation binding・probe 結果・token identity・opened snapshot の fingerprint を登録し、adapter 入口で exact identity まで検査。`s8b_attempt_registry.py:258-316` の issued-token / state fingerprint と同型 |
| A4 | v2 の等値 flag 解除は core 直呼びの受理集合を広げる | real | 採用 (C1b)。**core は v2 terminal を無条件拒否したままにし、adapter が実 bytes を検証した digest 集合を process-local capability として core へ渡す専用経路だけを開く** (replay: `load_attempt_registry(..., verified_terminal_evidence=<capability>)`、write: `record_attempt_terminal(..., verified_terminal_evidence=...)`)。D1522 の 3 段 test (通常 core は拒否 / 専用下層経路が実 bytes を再導出 / adapter がその経路を実際に呼ぶ) |
| A5 / B6 / B7 | 再導出 policy が排他・網羅でない、非有限値、field 間の到達可能性 | real | 採用 (C1b の契約 = 3 節の不変条件と precedence)。非有限値は runner を触らず証拠側で正規化 (6 節 2) |
| A6 / B1 | 証拠が attempt に束縛されていない、file-only 状態 | real | 採用。`attempt_binding` を契約へ追加 (3 節)。file-only (evidence あり row なし) は evidence-first 公開の**予定された crash 状態**として許容し、非保証として明記 (D1533 の形。6 節 3) |
| A7 / B5 | `campaign_record` の crash 順序と全 field 照合 | real | 採用。契約に exact key / 型表と「identity は reservation、計測 field は opened / sink、probe は launcher probe から再照合」を書く (3 節)。順序「純 record 構築 → evidence 公開 → terminal row → journal append」は C2 の境界 (5 節) |
| B3 | reserve → pre-probe と consumption marker の権限順 | real | 親裁定 (6 節 1): **ticket を pre-probe 前に消費し、marker と capture 用 observation capability の組を launcher へ渡す** (fragment 9 決定 2 「計測前 probe の競合 session も v2 台帳の対象」の帰結)。ユーザーは覆せる。C1a は reservation に marker を運ぶだけで順序を決めない |
| B4 | C1a 単独では v2 が半開き | real | 採用 (C1a)。v2 profile または marker 非 None を genesis / reserve の副作用前に `[s8b-launcher-v2-terminal]` で拒否。通る正例 = v1 profile + marker None |
| A8 | 既存 v2 genesis の非互換 (E2 が genesis bytes に入る) | real | 採用 (C1b)。共有 root の v2 世代在庫 0 件を land 条件に。tracked 0 件は実測済み |
| A9 | pre-probe skip 分岐の型と再開規則 | real | 採用 (C1a)。`captured=None` を許す classified state、`probe_after=None` / launch_failures 空 / capture・open failure なしを exact 要求、classified-failure observation → terminal (C1a では v1 の旧 API) |
| A10 / B14 | (P5) 棄却、C1b は A2α 級 | real | 採用。C1a 1 checkpoint (fix 2 巡見込み)、C1b 1 checkpoint (contract leaf → 2 本並列、fix 4〜6 巡見込み) |
| A11 / B16 | brief の anchor・node 数・DW-O13 の誤り | real | 採用。訂正は 7 節。実装には影響しない |
| A12 | plan 総括に非発火の逐語が無い | real (nit) | 採用。記録の文言 |
| A13 | post 専用の名前 | real (nit) | **不採用。** rename すると spawn-site 在庫 pin (`test_ccbench_spawn_sites.py:212`) を触る。同じ関数を 2 回呼ぶ形で pin 不変を優先 (docstring で pre / post 共用を明記) |
| B8 | 既存赤は 16 でなく 14 node | real | 採用 (C1a の期待赤は 4 節) |
| B9 | launcher fake が実 adapter と別契約 | real | 採用。**C1a:** fake token を `ScalePoint` 同形 (attribute `throughputs` / `notes` / `rep_observations`、open 時に sink を更新) へ変え、caller kwargs に launcher 私有 sink が足されることを fake capture が観測。**C1b:** fake に production の `require_sealed_terminal_evidence()` を呼ばせる |
| B11 | C2 は現 campaign seam のままでは動かない | real | 採用 (C2 境界、5 節)。C1a の `launch_floor_attempt` signature 変更は authority 引数の削除だけ |
| B12 | 変異 M4 / M6 / M7 / M11 / M16 の帰属不成立 | real | 採用。C1b の変異は次 wave の段 4 で再登録。C1a の変異は 4 節 |
| B13 | 親の 1 回目 focus の実行集合 | real | 採用。focus-1 = baseline と同じ 38 file (2-hop consumer 閉包) |
| B15 | durable 経路の全 reader を exact 化 | real | 採用 (C1b)。load 面 7 箇所の表 (`:974` prefix、`:1647` 予算、`:1687,1698` atomic、`:1883` read、`:1942,2439` snapshot、`:2791` resume) に正例 / 負例を 1 対 1 で当てる |
| A14 | D1533 の非保証を result.md へ | real | 裁定パッケージ (6 節 5) |
| A15 | D2 の動的 `RESULT_SCHEMA` fixture | real | 裁定パッケージ (6 節 5、前 wave の 4 を持ち越し) |

## 3. terminal 証拠の契約 v2 (固定。C1b が実体化、C2 が供給、D2 が再検証)

**文書:** `s8b-floor-terminal-evidence/v1`、canonical JSON (`attempt_registry_core.canonical_json_bytes`、sort_keys、`allow_nan=False`) の LF 無し bytes。
digest = sha256(bytes) を v2 terminal 行の新 field **`terminal_evidence_sha256`** に載せる。文書は `floor-attempt-registry-receipts/terminal-evidence/<digest>.json` へ
create-only (`allow_exact_retry=True`) で公開し、`_atomic_update_locked` の `prepare()` (registry staging の前) で公開する。v1 の event key 集合は不変。

**exact field (24):**

| field | 出所 (D1113: 呼び手は選べない) | 束縛 |
|---|---|---|
| `schema_version` | launcher 定数 | literal |
| `attempt_binding` | reservation + handle state | exact object `{freeze_sha256, protocol_sha256, schedule_sha256, slot (5 軸 exact + schedule_row_sha256), attempt_id, campaign_run_id, manifest_sha256, run_relpath, cell_id, classification_receipt_sha256, classification_event_sha256, observation_start_event_sha256}`。adapter が `_AttemptState`・claim・terminal 行の三者と照合 |
| `protocol` | reservation (normalized protocol 全体) | `canonical_protocol_sha256(protocol) == binding.protocol_sha256` (launcher で副作用前、adapter で再検査) |
| `mode` | reservation | `{"pilot","official"}` literal。adapter が durable claim の `mode` と等値 |
| `perf_preflight_receipt` | reservation (normalized | null) | 形の検査 + `use_perf_from_receipt` の再導出。manifest bytes への束縛は C2 が渡し D2 が再読 (6 節 4) |
| `expected_use_perf` | 機械導出 mirror | `== use_perf_from_receipt(perf_preflight_receipt)`、official + receipt 非 null + True は拒否 (campaign `_assert_perf_mode` と同じ)、capture kwargs `use_perf` (省略時 True) と等値 |
| `probe_before` | launcher 固定 argv | exact `{rc, stdout, stderr, competing}` |
| `probe_after` | 同上 | 同形 | null。**null ⇔ `probe_before.competing`** |
| `failure` | launcher | null | `{stage: "capture"|"open", exception_type, errno, message}` |
| `launch_failures` | token (`_launch_failure_evidence` 射影) | list。`failure.stage=="capture"` なら空 |
| `throughputs` | opened measurement (`ScalePoint.throughputs`) を私有 sink の qualified 列と照合 | 有限 float 列。非有限は null へ正規化し `nonfinite_count` に数える |
| `nonfinite_count` | 正規化時に数える | int ≥ 0 |
| `reps_expected` | `protocol["reps"]` | capture kwargs `reps` と等値 |
| `exec_failures` | 私有 sink から再導出 (rc ≠ 0 / 起動失敗の rep 数)。`notes` の regex は比較にだけ使う | opened なら `0..reps_expected`、`failure` 非 null なら `reps_expected` (unavailable projection と明記) |
| `repetition_evidence` | 私有 sink の open 後 snapshot (正規化済み) | opened なら長さ = reps_expected、それ以外は空 |
| `rep_integrity_failures` | `s8b_floor_stats._derive_rep_integrity` | opened なら exact int、それ以外 null |
| `session_cv_max` | `protocol["session_cv_max"]` | decimal 文字列 |
| `raw_output_sha256` | launcher が `raw_output_bytes` から計算 | adapter の deferred reader 再計算と等値。`== sha256(serialize_session_line(campaign_record))` |
| `report_sha256` / `observation_sha256` | 導出 (raw line digest / observed 時だけ `repetition_evidence` の canonical digest、他は null) | terminal builder の同名値は比較のみ |
| `finished_at` | launcher の注入 clock (`classified_at` と同じ callable) | text |
| `campaign_record` | terminal builder (session mapping 全体) | exact key / 型表 (`_finish_session` の emit と同じ 27 key)。identity field は reservation、計測 field (throughputs / exec_failures / rep_observations / rep_integrity_failures / reps_expected) は opened / sink、probe 組は launcher probe、`excluded_reason` / `session_median` / `valid` は再導出と**全件等値** |
| `self_report` | terminal builder | `{terminal_status, excluded_reason, primary_value}`。比較専用 |

**cross-field 不変条件 (1 つでも破れば `[s8b-terminal-evidence]` で拒否、`observed` へ落とさない):**
`probe_after is None` ⇔ `probe_before.competing` ⇔ (`failure` null ∧ `launch_failures` 空 ∧ `throughputs` 空 ∧ `repetition_evidence` 空 ∧ `rep_integrity_failures` null ∧ `exec_failures == 0`);
opened (`failure` null ∧ `probe_after` 非 null) ⇒ sink 長 = reps_expected ∧ `rep_integrity_failures` int ∧ `exec_failures` = sink 由来;
`failure` 非 null ⇒ measurement 無し ∧ `exec_failures == reps_expected`; `launch_failures` 非空 ∧ `exec_failures == 0` は矛盾 → 拒否;
`len(throughputs) + nonfinite_count + exec_failures == reps_expected` (opened 時)。

**再導出 (E1)。順序は campaign `_run_session` :6312-6323 と同じ。各枝は E2 の語と campaign の凍結語を別々に返し、辞書を持たない:**
1. `probe_before.competing ∨ probe_after.competing` → `retryable-failure` / `measurement_environment_conflict` (campaign: `competing_process`)
2. `failure` 非 null ∨ (`launch_failures` 非空 ∧ `exec_failures ≥ reps_expected`) → `retryable-failure` / `measurement_execution_unavailable` (campaign: `launch_failure`)
3. `0 < exec_failures < reps_expected` → campaign と同じく `launch_failure` の語で `measurement_execution_unavailable` (plan の sample 案は却下。campaign :6318-6322 と一致させる)
4. `rep_integrity_failures > 0` ∨ `nonfinite_count > 0` ∨ `assess_session.required_reason == nonfinite_or_partial_output` → `measurement_sample_incomplete` (campaign: `nonfinite_or_partial_output`)
5. `assess_session.required_reason == performance_anomaly` → `measurement_dispersion_exceeded` (campaign: `performance_anomaly`)
6. それ以外 → `observed` / null / primary = `assess_session.median`
`self_report` と `campaign_record.excluded_reason` が再導出の campaign 語と一致しなければ拒否。**E2 の 4 語** = `measurement_environment_conflict` /
`measurement_execution_unavailable` / `measurement_sample_incomplete` / `measurement_dispersion_exceeded` (`S8B_V2_RETRYABLE_FAILURE_REASONS`、v1 は空のまま)。
状態語: 理由あり = `retryable-failure`、理由なし = `observed`。`terminal-failure` / `not-consumed` は再導出で出さない。v2 の `require_terminal_reason_equals_classification`
は core では**外さない** (A4)。classification の echo は core で等値のまま、E2 の語との整合は adapter が実 bytes から 3 値 (classification reason / E2 reason / campaign reason) を
再導出して検査する。

**crash 後の権威:** (1) 台帳行 + receipts dir の bytes。(2) 行の digest が指す no-follow regular file を root lock 下で読み、filename / bytes digest / strict JSON / exact keys /
canonical bytes / attempt_binding を検査。(3) file から再導出した status / reason / primary / 3 digest / classification reason が行と一致した場合だけ受理。
row あり file なし・digest 不一致・内容不一致は拒否。file あり row なしは許容 (6 節 3)。

## 4. plan v2 — C1a (本 wave、実装子 1 本: launcher + launcher test)

所有: `orchestrator/campaign/s8b_floor_attempt_launcher.py`、`orchestrator/tests/test_s8b_floor_attempt_launcher.py`。`test_ccbench_spawn_sites.py:212` の pin は不変 (同じ `_owned_post_probe` を 2 回呼ぶ)。

1. **`FloorAttemptReservation`** (:54-69) に `protocol: Mapping`、`mode: str`、`perf_preflight_receipt: Mapping | None`、`consumption_marker: object | None` を足し、`slot_id` を 4 軸 | 5 軸 tuple にする。
   `_reserve` (:444-469) は `consumption_marker=` を adapter へ渡す。
2. **副作用前の検査 (genesis / reserve / subprocess の前):** `mode` literal、`canonical_protocol_sha256(protocol) == binding.protocol_sha256` (`s8b_floor_contract.canonical_protocol_sha256`)、
   `expected_use_perf = use_perf_from_receipt(receipt)` (`calibrator.perf_preflight`)、official + receipt 非 null + True は拒否、capture kwargs の `use_perf` (省略時 True) / `reps` が
   `expected_use_perf` / `protocol["reps"]` と等値。`protocol` / receipt / marker に callable が無い。
3. **v2 早期 gate:** `profile.schema is S8B_V2_SCHEMA_PROFILE` または `consumption_marker is not None` なら、genesis / reserve の前に
   `FloorAttemptLauncherError("[s8b-launcher-v2-terminal] v2 attempts require the sealed terminal evidence API")`。通る正例 = v1 profile + marker None。
4. **launcher 所有の分類 authority:** `_CLASSIFICATION_POLICY = {"schema": "s8b-floor-pre-output-classification/v1", "precedence": ["competing_process", "launch_failure"], "probe_argv": [...], "probe_timeout_s": 120.0}`、
   `_CLASSIFICATION_AUTHORITY = ClassificationAuthority(authority_id="s8b-floor-attempt-launcher/pre-output-classification/v1", authority_policy_sha256=sha256(canonical bytes))`。
   public `launch_floor_attempt` から `classification_authority` 引数を**削除**。`_launch_floor_attempt_for_test` は注入を残す。
5. **流れ:** `validate → ensure genesis → reserve → probe_before → (competing: captured=None, probe_after=None, launch_failures=()) | (private sink 生成 → capture (例外は `failure={stage:"capture",...}`、post-probe は finally 相当で必ず走る) → probe_after) → classify → open (例外は `failure={stage:"open",...}`) → sink snapshot (open 後) → terminal_builder → raw output seal → observation → record_attempt_terminal (旧 API、v1 だけ)`。
   `_DurablyClassifiedMeasurement` は `captured=None` を許し `open()` は None を返す。`_pre_observation_failure_reason` は `probe_before.competing ∨ probe_after.competing` → launch_failures → None。
   `_external_evidence_sha256` の payload に `probe_before` と nullable `probe_after` を入れる (schema を `s8b-floor-pre-output-evidence/v2` へ)。`_post_probe` は exact 4 key を要求 (余分 key 拒否)。
6. **`OpenedFloorAttempt`:** `post_probe` を `probe_before` / `probe_after` に分け、`failure` (stage 付き)、`repetition_evidence` (tuple、open 後 snapshot)、`expected_use_perf`、`reps_expected` を足す。`open_error` は `failure` へ統合。
7. **私有 sink:** `_capture` が allowlist 検査後に `rep_observations=<launcher 私有 list>` を足す。`_CERTIFIED_MEASUREMENT_KEYWORDS` は不変 (caller の `rep_observations` は従来どおり拒否)。
8. **test:** fake token を `ScalePoint` 同形 (`throughputs` / `notes` / `rep_observations` attribute、`open()` 時に sink を更新) へ。期待赤 (更新対象) = launcher 12 node 全部 (reservation の必須 field 追加による constructor error 11 + real genesis 1、うち挙動差は ordering 3 param + open error 1)。新設は 4 節末の変異を観測する node を含めて +12〜18 node。
   `test_attempt_registry_core_s8b_profile.py` / `test_s8b_attempt_registry.py` は**触らない** (C1a は v2 を開かない)。

**規模上限:** production +150〜220 / −40、test +250〜400。超えたら差し戻す。

**変異事前登録 (C1a、実装後に単一理由性を確認):**

| ID | 変異 (file: symbol) | KILLED 期待 node (実装子が命名) | 他 gate に遮られない理由 |
|---|---|---|---|
| M1 | pre-probe 競合分岐で capture を呼ぶ | `test_pre_probe_competition_terminalizes_without_capture` | fake capture の call 自体を観測 |
| M2 | sink snapshot を `open()` 前へ移す | `test_private_rep_sink_snapshot_occurs_after_token_open` | fake token が open 時にだけ sink へ書く |
| M3 | v2 早期 gate を外す | `test_v2_profile_is_rejected_before_any_registry_side_effect` | recorder fake が genesis / reserve call 0 件を観測 |
| M4 | public API に `classification_authority` 引数を復活させ caller 値を使う | `test_certified_api_owns_classification_authority` | signature 検査 + recorder が launcher 定数 id / digest を観測 |
| M5 | protocol digest 等値検査を外す | `test_reservation_rejects_protocol_not_bound_to_binding` | 他は valid、protocol の 1 値だけ変える |
| M6 | `expected_use_perf` を receipt でなく capture kwargs から取る | `test_use_perf_must_be_derived_from_receipt` | receipt = unavailable、kwargs use_perf=True の不一致だけ |
| M7 | `_pre_observation_failure_reason` が `probe_before.competing` を無視 | `test_pre_probe_competition_classifies_as_competing` | post は非競合、launch_failures 空 |
| M8 | `_external_evidence_sha256` の payload から `probe_before` を落とす | `test_external_evidence_digest_binds_both_probes` | probe_before だけ変えて digest 差を観測 |
| M9 | `_post_probe` の exact key 検査を緩める (余分 key 受理) | `test_probe_result_requires_exact_keys` | 直接呼び |
| M10 | capture 例外を `failure` にせず伝播させる | `test_capture_exception_terminalizes_with_stage_capture` | fake capture が raise、post-probe と terminal が走ることを観測 |
| M11 | `reps` 等値検査を外す | `test_reservation_rejects_reps_not_equal_to_protocol` | 他は valid、reps だけ差 |
| M12 | `failure.stage="open"` の open 例外で sink snapshot を取らない → 取る、へ (snapshot は空であるべき) | `test_open_failure_yields_empty_repetition_evidence` | fake token open が raise しつつ sink へ書く |

## 5. 境界の固定 (実装しない部分)

- **C1b (次 wave):** contract leaf `orchestrator/campaign/s8b_terminal_evidence.py` (3 節の exact dataclass、`seal_terminal_evidence(reservation, opened, terminal)` = launcher 私有 issuer、
  `require_sealed_terminal_evidence(value) -> ValidatedTerminalEvidence`、projection の pure 関数) を先に固定 → unit1 (launcher 側の発行 + launcher test) / unit2 (core の capability 経路、
  profile の E2 と validator、adapter の `record_sealed_attempt_terminal(observation, evidence)`、artifact 検査、load 面 7 箇所、その test) を並列。
- **C2:** `_finish_session` を純 `_build_session_record()` と journal append に分け、順序「純 record → evidence 公開 → terminal row → journal append」。ticket は pre-probe 前に消費し、
  marker + capture 用 observation capability の組を reservation に載せる。`measure_fn` / `probe_fn` seam を持つ campaign test 476 node のために、certified public API と別の非認証 seam (`_launch_floor_attempt_for_test` の形) を campaign 側に明示する。
  receipt を manifest canonical bytes から取る。producer capture → `assemble_result(attempt_registry=proof)`、`RESULT_SCHEMA` v5。
- **D2:** receipt ↔ manifest の再検証、D1533 非保証文の result.md、動的 `RESULT_SCHEMA` fixture の固定。

## 6. ユーザーへ返す裁定パッケージ (親裁定は覆せる)

1. **pre-probe 除外 attempt でも admission ticket を消費する** (親裁定)。理由: fragment 9 決定 2 が計測前 probe の競合 session を v2 台帳の対象に含めた。v2 予約は marker (= ticket 消費後) を要求するため、
   台帳化には消費が先。代案 = pre-probe 除外専用の非 consumption 予約権限を admission に新設 (受理集合と予算の意味が変わる)。
2. **非有限 throughput は runner (`benchparse._num`) を触らず証拠側で null + `nonfinite_count` に正規化する** (親裁定)。代案 = `_num` を `math.isfinite` で閉じる (C1 所有外、既存計測値域を変える)。
3. **evidence file あり・terminal row なしは許容し非保証として明記する** (親裁定)。evidence-first 公開の予定された crash 状態で、resume は `allow_exact_retry` で再公開する。代案 = slot 宛 pending index を作り replay を recoverable failure で止める (規律 5 に照らして今は作らない)。
4. **perf receipt の manifest 束縛は C2 (供給) + D2 (再検証) に置く。** C1 は形と機械導出だけ。
5. 持ち越し: D1533 の非保証を result.md へ載せる所有 (C2 / D2)、D2 の動的 `RESULT_SCHEMA` fixture (B2 / D1 の 4)、B2 / D1 の 1・2・5、A2α / A1' / B1 の未裁定。

## 7. brief の訂正 (両レンズの実測)

- launcher anchor: `FloorAttemptTerminal :126`、`_owned_post_probe :238`、`_external_evidence_sha256 :362`、`_pre_observation_failure_reason :378`、`_launch_floor_attempt :548`、terminal call `:637`。
  `_finish_session :6346`、`S8B_V2_RETRYABLE_FAILURE_REASONS :533`、result schema literal は contract `:35-36`。
- test 件数: 7 / 75 / 68 / 328 は関数数。parametrize 展開後の node は 12 / 111 / 108 / 476 (campaign は 336 関数)。
- DW-O13: 下層に素材はあるが production launcher carrier は未実装 (probe_before / 私有 sink / protocol / mode / receipt は reservation / opened に無い)。fake test は production 到達性の証拠ではない。
- 既存 v2 terminal 関連 pin は 4 node、うち plan どおりなら赤は 14 node (C1b 時)。C1a の赤は launcher 12 node。
