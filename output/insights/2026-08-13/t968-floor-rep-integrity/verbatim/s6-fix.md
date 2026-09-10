## 総括

- R1〜R10 の修正を実装し、全項目を「実装済み・未実走」とした。
- 証跡免除を構造的事実に限定し、全 session の `exclusion_class` を再導出する。
- `seq` 等の正規化を廃止し、非負 exact int／exact bool を必須化した。
- v3 resume の早期 return、holdout caller、ratified fixture、stats fixture を修正した。
- M1／M2／M4／M12 は単一 anchor が各 1 箇所だけ存在する状態へ再照準した。
- 13 変更ファイルの構文、AST、NFC、`git diff --check` は静的検査済み。
- pytest・build・変異 harness は実行していない。結果は「実装済み・未実走」である。
- docs、`output/`、commit は変更しておらず、HEAD は `31b004b7` のままである。

### 実装内容

主要修正は [s8b_floor_stats.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_stats.py:424) と [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:862) に入れた。

- `_REQUIRED_SESSION` に `exclusion_class` を追加。
- `exclusion_class` の再導出・一致検査を証跡免除分岐の外へ移動。
- pre-probe competing は `probe_before.competing is True` かつ `probe_after is None`、measure 例外は非競合の前後 probe、全 rep 起動失敗、固定 `launch_failure` と整合するときだけ免除。
- `strict_probe` の永続化値を exact bool に変更。
- `seq`、`reps_expected`、`exec_failures` は非負 exact int、`retry` は exact bool として検査し、`int()`／`bool()` を廃止。
- v3 journal は v2 移行判定より先に return。測定済み v2 の拒否は維持。
- `_finish_session` の重複した本数 gate を除き、M2 の単一変異が実在する構造に変更。
- [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_holdout_freeze.py:1359) は指定された呼び出し 1 行だけに `expected_use_perf=True` を追加。
- `use_perf` meta-test は期待リストを変えず、対象 4 関数だけへ限定。
- ratified production-emitter fixture と v2 freeze fixtureへ証跡を追加し、既存の ratified 3 件と stats の tuple 偽赤を実装側で補正した。

### R1〜R10 対応表

未実走のため、実装済みでも `closed` とは申告しない。

| 所見 | 状態 | 対応 |
|---|---|---|
| R1 | partial | 全 session の class 再導出、必須 key、competing／launch 負例を実装 |
| R2 | partial | 構造的免除 helper と測定済み偽装攻撃の負例を実装 |
| R3 | partial | exact 型検査と指定された 4 値の負例を実装 |
| R4 | partial | meta-test を対象関数へ限定。AST 上の 4 caller は期待集合と一致 |
| R5 | partial | M7 を kill 集合から除外し、既存構造テストは diagnostic pin として維持 |
| R6 | partial | M1 の `if complete` anchor を一意化 |
| R7 | partial | M2 の二重 gate を除き、一箇所変異で動作が変わる形へ再照準 |
| R8 | partial | M4 の `incomplete` 資格化 anchor を一意確認 |
| R9 | partial | M12 を exact-int→`isinstance`、`returncode=False` で fail-open する形へ再照準 |
| R10 | partial | 下記に parameter suffix 込みの完全 nodeid 集合を列挙 |
| regressed | なし | 静的検査範囲では確認なし |

### 変異 ID → 完全 nodeid 集合

M7 は diagnostic sensitivity pin へ降格済みであり、kill 対象には含めない。

- M1、M2

  - `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_positive_control_default_measure_point[nonzero_rc]`
  - `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_positive_control_default_measure_point[missing_cycles]`

- M3

  - `orchestrator/tests/test_calibrator.py::test_measure_point_rep_observations_are_indexed_across_timeout_exception_and_rc`

- M4

  - `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_missing_each_perf_event_excludes_session[LLC-load-misses]`
  - `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_missing_each_perf_event_excludes_session[LLC-loads]`
  - `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_missing_each_perf_event_excludes_session[instructions]`
  - `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_missing_each_perf_event_excludes_session[cycles]`
  - `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_positive_control_default_measure_point[missing_cycles]`

- M5

  - `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_negative_perf_counter`

- M6

  - `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_unknown_or_missing_rep_evidence[unknown]`

- M8

  - `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_integrity_violation_with_valid_claim`

- M9

  - `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_false_rep_integrity_exclusion`

- M10

  - `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_perf_required_not_required_claim`

- M11

  - `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_counter_status_missing_contradiction`

- M12

  - `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_bool_in_rep_observation[returncode-False]`

- M13

  - `orchestrator/tests/test_s8b_floor_campaign.py::test_resume_v3_rejects_session_without_rep_integrity_evidence`

- P1

  - `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_positive_control_default_measure_point[no_perf]`

- P2

  - `orchestrator/tests/test_s8b_floor_campaign.py::test_resume_allows_pre_measure_v2_journal_transition`

- P3

  - `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_positive_control_default_measure_point[clean]`

- P4

  - `orchestrator/tests/test_s8b_floor_stats.py::test_verify_accepts_zero_perf_counters`

- P5

  - `orchestrator/tests/test_calibrator.py::test_measure_point_survives_partial_rep_failure`

### 追加・変更 nodeid

以下は関数単位でまとめ、parameterized node は suffix 集合を併記する。

- `test_calibrator.py`

  - `test_measure_point_survives_partial_rep_failure`
  - `test_measure_point_rep_observations_are_indexed_across_timeout_exception_and_rc`
  - `test_measure_point_rep_observations_no_perf_are_not_required`
  - `test_perf_raw_evidence_rejects_duplicate_and_infinite_values`

- `test_s8b_floor_campaign.py`

  - `test_resume_allows_pre_measure_v2_journal_transition`
  - `test_resume_rejects_v2_once_measurement_event_exists[session-start|session]`
  - `test_resume_v3_rejects_session_without_rep_integrity_evidence`
  - `test_rep_integrity_positive_control_default_measure_point[clean|nonzero_rc|missing_cycles|no_perf]`
  - `test_rep_integrity_missing_each_perf_event_excludes_session[LLC-load-misses|LLC-loads|instructions|cycles]`
  - `test_no_perf_rep_integrity_requires_zero_rc_and_marks_counters_not_required`
  - `test_rep_integrity_precedence_uses_completed_measure_evidence[post_competing-competing_process|launch-launch_failure|integrity-rep_integrity_failure]`
  - `test_rep_integrity_precedes_partial_in_runner_branch_order`
  - `test_production_use_perf_keyword_call_sites_are_a_closed_set`
  - `test_end_to_end_golden_floor_values_and_tamper_detection`
  - `test_verify_floor_artifact_binaries_positive_and_negative`

- `test_s8b_floor_stats.py`

  - `test_verify_requires_expected_use_perf_keyword_argument`
  - `test_verify_rejects_integrity_violation_with_valid_claim`
  - `test_verify_rejects_false_rep_integrity_exclusion`
  - `test_verify_rejects_exempt_session_exclusion_class_tamper[competing|launch]`
  - `test_verify_rejects_completed_measure_disguised_as_unmeasured_exemption`
  - `test_verify_rejects_normalizable_session_scalar_types[seq-string|reps-float|failures-string|retry-float]`
  - `test_verify_rejects_perf_required_not_required_claim`
  - `test_verify_rejects_counter_status_missing_contradiction`
  - `test_verify_rejects_bool_in_rep_observation[returncode-False|rep_index-False]`
  - `test_verify_rejects_negative_perf_counter`
  - `test_verify_rejects_unknown_or_missing_rep_evidence[unknown|missing_observation]`
  - `test_verify_accepts_zero_perf_counters`

- `test_s8b_ratified_verify.py`

  - `test_result_excluded_projection_rederived_from_journal`

共有 fixture の変更には単独 nodeid がない。`_EmitterScalePoint`、`_session_rows`、`s8b_v2_freeze_fixture._synthetic_floor_result` を消費する各 test へ波及する。

### 静的検査と境界

実施済み:

- 変更 13 ファイルの `python3 -m py_compile`
- 変更 13 ファイルの `ast.parse`
- 変更 13 ファイルの NFC 検査
- `git diff --check`
- M1／M2／M4／M12 anchor が各 exact 1 件であること
- v3 早期 return が測定 event 拒否より前にあること
- production の `verify_floor_artifact` caller 全件が `expected_use_perf` を明示すること
- no-touch 定数、4 理由固定順、formula／protocol／manifest schema が HEAD と同一であること
- docs／`output/` 差分なし
- holdout generator の差分が指定された 1 行だけであること

pytest、build、変異 harness は一切実行していない。したがって検査結果を「緑」とは報告しない。状態は明確に **実装済み・未実走** である。

既存テストの assert 期待値は一つも変更していない。M12 の入力 fixture を裁定どおり `True` から `False` へ再照準し、共有 fixture に新必須 field を追加しただけで、反転、緩和、skip、削除はない。

所有外への静的波及候補は、holdout v2 candidate の 3 consumer、ratified verifier の production-emitter consumer、resume／finalize consumer、`ScalePoint.rep_observations=None` を使う非 floor calibrator caller、stats の共有 `_sess`、v2 freeze fixture consumer である。`test_s8b_approved.py` の file 選択固有 ImportError には触れていない。