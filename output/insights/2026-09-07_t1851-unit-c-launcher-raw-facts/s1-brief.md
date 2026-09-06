# [T-1851] 段 1 brief — 実装単位 C (起動層の実際の呼び手を v2 台帳へ繋ぐ) の第 1 checkpoint C1: terminal 証拠の契約と封印 terminal API

日付: 2026-09-05。branch `worktree-dev-wave-t1851-unit-a`。継承 tip `9f64a3d44` (B2 / D1 の記録 + 段 8)。
main 取り込み後 tip `04f06d032` (local main `97ee3cd3a`、両親が共に触った file 0、gitlink 一致、integrator)。

## scope

台帳配線 3 task 閉包の 6 段分割 `B1 → A → B2 → D1 → C → D2` の **C** に入る。A2β 7 節の裁定 2 (fragment 9 の第 2 決定) により、
C の brief は **terminal 証拠の契約を先に短く固定**し、その契約に依存する部分を後ろへ置く。C は 2 checkpoint に割る (下の (P1))。

- **C1 (本 wave):** (a) terminal 証拠文書 v1 の契約 (exact field 集合と canonical 化)、(b) 起動層 (`s8b_floor_attempt_launcher`) が
  生の事実から証拠を封印して発行する evidence-bound handle と、launcher 私有の `rep_observations` sink、pre-probe の起動層所有、
  (c) 台帳層の**封印 terminal API (E1)**: v2 terminal 行を封印証拠から再導出し、自己申告 field は比較にだけ使う。
  A2α の二層無条件拒否 (`[s8b-v2-terminal] v2 terminal requires the sealed evidence API`、S5 / S6) を「封印 API 以外を拒否」へ置き換える、
  (d) **台帳専用理由語彙 4 語 (E2)** を validator と同じ commit で active にする、(e) 証拠文書の durable 化 (create-only 公開) と
  terminal 行への digest 束縛、crash 後に権威として読み直す bytes の規則。
- **C2 (次 wave、本 wave は境界だけ固定):** campaign `_Runner._run_session` が `launch_floor_attempt()` を呼ぶ production 配線
  (v2 profile / genesis を protocol + schedule から組む、admission の consumption marker、binding)、producer の
  `capture_attempt_registry_prefix` → `assemble_result(attempt_registry=proof)`、`RESULT_SCHEMA` の v5 切替、pending 再読、resume。
  その後に B2 / D1 の terminal 依存部分 (coverage 全単射、`finished_at`、attempts projection) と D2 (consumer 3 面)。
- 本 wave が実装しないもの: campaign (`s8b_floor_campaign.py`) の変更、`RESULT_SCHEMA` の値変更、凍結成果物、v1 台帳の reader / writer。

## terminal 証拠の契約 (親が固定する。plan・レンズは field の過不足と到達可能性を攻撃せよ)

- **文書:** `s8b-floor-terminal-evidence/v1`、canonical JSON 1 行 (`attempt_registry_core.canonical_json_bytes`、sort_keys、`allow_nan=False`)。
  digest = sha256(canonical bytes) を **v2 terminal 行の新 field `terminal_evidence_sha256`** に載せる (B2 / D1 は v2 terminal 行の exact reader を
  まだ固定していないので、この追加は手戻りにならない — fragment 9 第 2 決定の理由 4)。文書自体は classification receipt と同じ形で
  receipts dir へ create-only 公開し (durable)、replay 時の検査は「行の digest → 実在 file の bytes → 再導出した status / reason / primary が
  行と一致」の向きで行う。**crash 後の権威は台帳行 + receipts dir の bytes** であり、process メモリや campaign journal ではない。
- **exact field (親案、plan が現物で過不足を判定):** `schema_version`、`expected_use_perf` (bool。verified mode と perf-preflight receipt から
  `calibrator.perf_preflight.use_perf_from_receipt` で機械導出。campaign `_assert_perf_mode` :448 と同じ関数)、`mode` (`pilot` / `official`)、
  `probe_before` (launcher 固定 argv の結果 `{rc, stdout, stderr, competing}` exact)、`probe_after` (同形 | null。pre-probe 競合で capture を
  走らせなかった session は null)、`launch_failures` (token の `launch_failures` を `_launch_failure_evidence` で射影した list)、
  `throughputs` (opened measurement の有限 float 列)、`reps_expected`、`exec_failures`、`repetition_evidence` (launcher 私有 sink の snapshot)、
  `rep_integrity_failures` (int | null)、`session_cv_max` (protocol の decimal 文字列)、`raw_output_sha256` (campaign の canonical session line の
  digest。terminal 行の同名 field と一致必須)、`self_report` (campaign の terminal builder が申告した `terminal_status` / `excluded_reason` /
  `primary_value` の 3 つ。**比較にだけ使う**)。
- **再導出 (E1 の policy、順序は campaign `_run_session` :6312-6323 の precedence と同じ):** `measurement_environment_conflict` ⇐
  `probe_before.competing` または `probe_after.competing`; `measurement_execution_unavailable` ⇐ open 失敗、または `launch_failures` 非空で
  `exec_failures >= reps_expected`; `measurement_sample_incomplete` ⇐ `0 < exec_failures < reps_expected`、`rep_integrity_failures > 0`、
  `len(throughputs) != reps_expected`、非有限・非正値; `measurement_dispersion_exceeded` ⇐ `assess_session` の CV > `session_cv_max`。
  理由なしなら `observed`、primary は `assess_session` の median。**理由の語は呼び手が選べず、`excluded_reason → ledger reason` の辞書を
  権威にしない (D1113)。** self_report と再導出が食い違えば `[s8b-v2-terminal-evidence]` で fail-closed 拒否 (規律 2 / 3、構造化理由)。
- **E2 の 4 語** (A2α 14 節の候補、親裁定で確定): `measurement_environment_conflict` / `measurement_execution_unavailable` /
  `measurement_sample_incomplete` / `measurement_dispersion_exceeded`。`S8B_V2_RETRYABLE_FAILURE_REASONS` に入れ、v1 の
  `S8B_RETRYABLE_FAILURE_REASONS` (空) と凍結 4 語 (`competing_process` 等) は変えない。

## 確定済みユーザー裁定 (不変)

- D1113 (理由は呼び手が選べない、台帳専用の閉じた語彙、封印 record から機械導出)、D1114 / D1336 (production 呼び手 0 の gate は land しない —
  本 wave も land しない、D1341)、D1194 / D1337 / D1340 / D1342、D1522 (下層の実体を名指しする直接検査)、D1530 (権威束縛は本番の呼び手と同じ
  変更単位)、D1533 (非保証の明記)。fragment 9 の 3 決定 (E1 / E2 は単位 C、証拠の意味規則 3 点、分類 claim / 回復行は囲まない)、
  fragment 10 (prefix inspector は exact 世代 1 つ)。D95: 実装面は Codex author。

## 不変条件

- v1 台帳 (1 段 path、schema v1) の reader / writer / filename digest は 1 byte も変えない。v1 の `record_attempt_terminal` /
  `record_classified_failure_terminal` は v1 で従来どおり通り、v2 では封印 API 以外を拒否し続ける。
- `RESULT_SCHEMA` の値は v4 のまま。producer の出力 bytes は変えない。凍結成果物・trust root・`FROZEN_MANIFEST` に触れない。
- launcher の certified API は caller 提供の callback・値選択を増やさない。`_CERTIFIED_MEASUREMENT_KEYWORDS` に `rep_observations` を足さない
  (sink は launcher 私有)。`post_probe` capability の封印は維持し、pre-probe も同じ固定 argv・同じ capability で行う。
- 新 gate はすべて exact / fail-closed。「証拠が無ければ skip」の形を作らない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) C は C1 / C2 の 2 checkpoint に割る。** 理由: 規模の見積りが 2 wave 連続で半分に下振れ (A2α 10 節)、campaign は 8,645 行 + test
  14,020 行 / 328 node で、launcher 配線 (probe_fn / measure_fn の seam を持つ test 群) は単独で 1 wave。fragment 9 が E1 を「C の中で」と
  定めた理由 (bytes・digest の結合・resume 時の再読込は起動層無しに定義できない) は、起動層 = launcher を C1 に含めることで満たす。
  plan が規模を実測し、C2 の一部 (例: producer capture の thin wrapper) を C1 に足せるなら足す。
- **(P2) pre-probe を launcher が所有する。** 現行 `_run_session` は pre-probe 競合で capture を走らせず session を閉じる (:6242-6255)。
  launcher は現在 post-probe しか持たない。証拠の契約が `probe_before` と nullable `probe_after` の exact 組を要求する (fragment 9) ので、
  launcher の流れを `reserve → pre-probe → (競合なら capture せず classify) → capture → post-probe → classify → open → build → seal → terminal`
  にする。spawn-site 在庫 (`test_ccbench_spawn_sites.py:212` の `_owned_post_probe: 1`) は同じ関数を 2 回呼ぶ形なら不変、別関数なら pin を
  追随させる。
- **(P3) 封印 API の形は evidence-bound handle。** launcher が `OpenedFloorAttempt` + terminal builder の戻りから `SealedTerminalEvidence`
  (frozen、process-local seal、campaign へ返さない) を作り、`s8b_attempt_registry.record_sealed_attempt_terminal(observation, evidence)` が
  受ける。keyword-only 引数で生の値を受ける形は D1113 から遠い (fragment 9)。`record_sealed_classified_failure_terminal()` は作らない
  (非 observation の終了経路を新設しないため。launcher は ClassifiedFailure も observation union で閉じる :607-615)。
- **(P4) 状態語の対応。** 理由あり = `retryable-failure` (v2 は `retryable_terminal_opens_next_attempt=False` なので次 attempt は開かず、測り直し軸
  `measurement_ordinal` の予約は C2 / 別裁定)。理由なし = `observed`。`terminal-failure` / `not-consumed` は本 wave の再導出では出さない。
  plan が `TransitionPolicy` (`require_terminal_reason_equals_classification=True`) との整合を現物で確かめよ: pre-observation reason
  (`competing_process` / `launch_failure`) を持つ classification に対し、terminal の `failure_reason` は台帳語彙 (E2) になるので、
  等値要求の意味を「classification の reason から E2 へ機械写像した値と一致」へ定義し直す必要がある。**辞書を権威にしない D1113 との両立は
  plan の必答。**
- **(P5) 1 wave に収まる。** 実装子 2 本 (unit1 = launcher + 証拠文書 + launcher test、unit2 = core / profile / registry の封印 API + E2 + test)。
  production +400〜700 行、test node +40〜70。境界の signature (`SealedTerminalEvidence` の exact field と seal、`record_sealed_attempt_terminal`
  の引数) は plan が先に固定し、unit1 / unit2 は file 所有で割る。
- **(P6) 証拠文書の durable 化は receipts dir への create-only 公開。** 既存 `_publish_create_only` / `_receipt_path` (:1430) を再利用し、
  terminal 行の `terminal_evidence_sha256` で名指しする。台帳の側 artifact を増やすので、`_assert_classification_artifacts` (:2059) と同型の
  replay 検査 (`_assert_terminal_evidence_artifact`) を core / adapter に置き、行と file の不一致を拒否する。

## 実アンカー表 (tip `04f06d032`)

| file | symbol / 現行行 | 本 wave の扱い |
|---|---|---|
| `orchestrator/campaign/s8b_floor_attempt_launcher.py` (701 行) | `_CERTIFIED_MEASUREMENT_KEYWORDS` :32、`OpenedFloorAttempt` :114、`FloorAttemptTerminal` :123、`_owned_post_probe` :232、`_external_evidence_sha256` :350、`_pre_observation_failure_reason` :366、`_capture` :429、`_launch_floor_attempt` :527、`record_attempt_terminal` 呼出し :628、`launch_floor_attempt` :648 | C1 (b): pre-probe、私有 sink、証拠の封印、封印 API 呼出し |
| `orchestrator/campaign/s8b_attempt_registry.py` (3,122 行) | `_receipt_path` :1430、`_assert_classification_artifacts` :2059、`classify_attempt` :2147、`_assert_observation_row` :2510、`_reject_legacy_v2_terminal` :2536、`record_attempt_terminal` :2544、`record_classified_failure_terminal` :2605 | C1 (c)(e): 封印 API の新設、S6 拒否の置換、証拠 artifact の replay 検査 |
| `orchestrator/campaign/attempt_registry_core.py` (2,131 行) | `record_attempt_terminal` :1971 (`failure_reason` 引数、terminal_keys :2032-2038)、`validate_attempt_registry_prefix_proof` (B2 / D1) | C1 (c): v2 terminal 行の新 field、再導出 validator の core 側 |
| `orchestrator/campaign/s8b_attempt_profile.py` (684 行) | `_S8B_EVENT_KEYS["terminal"]` :445、`_S8B_V2_EVENT_KEYS` :490、`S8B_V2_RETRYABLE_FAILURE_REASONS` :532、`_reject_unsealed_s8b_v2_terminal` :556、`make_s8b_v2_domain_profile` :639 (`terminal_row_validator` :683) | C1 (c)(d): v2 terminal key、E2、validator の差替え |
| `orchestrator/campaign/s8b_floor_stats.py` | `assess_session` :127、`SessionRecord` :172、`REP_INTEGRITY_EXCLUSION_CLASS` :62 | 再導出が呼ぶ純関数。変更なし |
| `orchestrator/calibrator/runner.py` | `capture_measure_point` :803 (`rep_observations` 引数)、`classify_competing_probe` :327 | 変更なし。sink と probe の実体 |
| `orchestrator/campaign/s8b_floor_campaign.py` | `_assert_perf_mode` :448、`strict_probe` :1695、`_run_session` :6213-6340 (precedence :6312)、`_finish_session` :6345 | **変更しない** (C2)。再導出 policy の写し元 |
| test | `test_s8b_floor_attempt_launcher.py` (7 node、`_RecorderRegistry.record_attempt_terminal` :158)、`test_s8b_attempt_registry.py` (75 node、v2 拒否 pin :3101-3102)、`test_attempt_registry_core_s8b_profile.py` (68 node、拒否 pin :2285-2294)、`test_ccbench_spawn_sites.py:212` | 既存 file へ足す。supersede してよい pin = A2α 14 節の 2 箇所 + spawn-site 在庫 |

## DW-O08 / O09 / O10 / O13

- DW-O08: submodule 初期化済み (`dev_wave_submodule_init.py` rc=0、gitlink `511c9538e`)。
- DW-O09: `s8b-floor-result/v4` の pin は前 wave と同じ (contract :34、`test_s8b_floor_contract.py:180`、`test_s8b_floor_stats.py:602,1921`)。本 wave は
  `RESULT_SCHEMA` を変えないので発火しない。v2 terminal 行の key 集合を pin する test (`test_attempt_registry_core_s8b_profile.py` の
  event_keys 検査) は plan が列挙する。tracked な v2 台帳 bytes は `output/` に 0 件。
- DW-O10: producer の出力 bytes は不変なので発火しない。
- DW-O13: 証拠の入力 field はすべて現物に実在する (`OpenedFloorAttempt` の 6 field、token の `launch_failures`、`capture_measure_point` の
  `rep_observations` sink、`use_perf_from_receipt`、`assess_session`)。ただし **production の呼び手は 0 件のまま** (D1114 / D1341 が予定する状態)。
  到達可能な値域は launcher test の fake token と registry test の実台帳 (genesis + reservation + classification + observation-start) で組む。
  「効いている」と書いてはならない。

## 成果物の形と DW-G05

放置時: v2 terminal が永久に閉じたままでは単位 C2 の配線が terminal を書けず、certified 選択は台帳束縛の無いまま (D1194 の「謳うだけで発火しない」)
が続く。既存 certified の値・受理集合・参照は本 wave で変わらない。

成果物: 実装 commit (Codex author 2 本 + fix)、変異 matrix (事前登録は段 4)、焦点走 + 受入全走 child-green、insight README、worklog / decisions
fragment (E2 の語と証拠契約は D 候補)。D1341 により land しない。

## 実測環境

focus 走は login node / 自動 dispatch、受入全走は `tools/dev_wave_wait.py acceptance` (D612 上書き 3600/600)。新規 Pegasus 実行体を要する実測は
無い。変異は harness 直接 + repo 外退避。
