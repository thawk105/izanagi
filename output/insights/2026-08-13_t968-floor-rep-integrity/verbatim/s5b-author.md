## 総括

- 先行差分を全件監査し、床値 rep 完備性の実装とテストを補完した。
- 既定 `measure_point` 経路の positive control は、実 subprocess のみを差し替える構成になっている。
- M1〜M13、P1〜P5 に対応するテスト node を静的に確認した。
- `expected_use_perf` は署名上も必須の keyword-only 引数にした。
- counter は非負の exact int のみ受理し、bool・小数・負値・重複・欠損を fail-closed にした。
- 構文、AST、import、NFC、差分形式、no-touch 境界を静的検査済み。
- pytest は実行していない。状態は明確に「実装済み・未実走」である。
- no-touch の旧 holdout generator caller 1 件だけ、必須引数化との衝突が残るため親裁定が必要である。

### 実装結果

先行実装から次をそのまま採用した。

- [model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/calibrator/model.py) の optional `ScalePoint.rep_observations` carrier。
- runner の indexed observation 事前確保、rc・raw perf・throughput の収集、parser と独立した重複検査。
- campaign の qualified throughput 射影、session 全体無効化、journal/result への結線、precedence。
- v2 測定済み journal の拒否と、測定前 v2 journal の v3 transition。
- result/journal schema v3 化。protocol、manifest、formula は据置。
- verifier の observation、failure count、qualified throughput、counter status の独立再導出。
- ratified verifier の exact-key consumer と再射影。
- v3 fixture、既定 closure の journal 結線、positive/negative control 群。

今回、先行差分へ追加・修正した箇所は次のとおり。

- `_perf_raw_values` の `int(float(...))` を廃止し、小数や `inf` を整数へ丸めず欠損にした。
- observation opt-in 経路では timeout 以外の通常例外も logical rep の `returncode=None` 証跡として保存した。opt-in しない既存 caller の例外契約は維持した。
- `verify_floor_artifact(..., *, expected_use_perf: bool)` を署名上も必須化した。
- M3 に timeout、通常例外、非 0 rc、成功の 4 logical rep を固定した。
- M6 に observation 件数欠落を追加した。
- M7 の分岐順変異を直接検出する AST node を追加した。
- positive control 挿入時に移動していた既存 `assert seen` を元のテストへ戻した。
- raw counter の小数拒否と必須引数署名をテストへ固定した。

### 変異 ID → nodeid

- M1 → `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_positive_control_default_measure_point[nonzero_rc]`
- M2 → 同 node
- M3 → `orchestrator/tests/test_calibrator.py::test_measure_point_rep_observations_are_indexed_across_timeout_exception_and_rc`
- M4 → `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_missing_each_perf_event_excludes_session[LLC-load-misses]`、`[LLC-loads]`、`[instructions]`、`[cycles]`
- M5 → `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_negative_perf_counter`
- M6 → `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_unknown_or_missing_rep_evidence`
- M7 → `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_precedes_partial_in_runner_branch_order`
- M8 → `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_integrity_violation_with_valid_claim`
- M9 → `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_false_rep_integrity_exclusion`
- M10 → `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_perf_required_not_required_claim`
- M11 → `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_counter_status_missing_contradiction`
- M12 → `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_bool_in_rep_observation`
- M13 → `orchestrator/tests/test_s8b_floor_campaign.py::test_resume_v3_rejects_session_without_rep_integrity_evidence`
- P1 → `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_positive_control_default_measure_point[no_perf]`
- P2 → `orchestrator/tests/test_s8b_floor_campaign.py::test_resume_allows_pre_measure_v2_journal_transition`
- P3 → `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_positive_control_default_measure_point[clean]`
- P4 → `orchestrator/tests/test_s8b_floor_stats.py::test_verify_accepts_zero_perf_counters`
- P5 → `orchestrator/tests/test_calibrator.py::test_measure_point_survives_partial_rep_failure`

M7 の動作側補助 node は `test_rep_integrity_precedence_uses_completed_measure_evidence`。post-probe competing、launch、integrity の各場合に証跡が残り、`valid=False`、median `None` になることを固定している。

### 追加・直接変更した nodeid

`test_calibrator.py`:

- `test_measure_point_survives_partial_rep_failure`
- `test_measure_point_rep_observations_are_indexed_across_timeout_exception_and_rc`
- `test_measure_point_rep_observations_no_perf_are_not_required`
- `test_perf_raw_evidence_rejects_duplicate_and_infinite_values`

`test_s8b_floor_campaign.py`:

- `test_resume_allows_pre_measure_v2_journal_transition`
- `test_resume_rejects_v2_once_measurement_event_exists`
- `test_resume_v3_rejects_session_without_rep_integrity_evidence`
- `test_rep_integrity_positive_control_default_measure_point`
- `test_rep_integrity_missing_each_perf_event_excludes_session`
- `test_no_perf_rep_integrity_requires_zero_rc_and_marks_counters_not_required`
- `test_rep_integrity_precedence_uses_completed_measure_evidence`
- `test_rep_integrity_precedes_partial_in_runner_branch_order`
- `test_end_to_end_golden_floor_values_and_tamper_detection`
- `test_verify_floor_artifact_binaries_positive_and_negative`

`test_s8b_floor_stats.py`:

- `test_verify_requires_expected_use_perf_keyword_argument`
- `test_verify_rejects_integrity_violation_with_valid_claim`
- `test_verify_rejects_false_rep_integrity_exclusion`
- `test_verify_rejects_perf_required_not_required_claim`
- `test_verify_rejects_counter_status_missing_contradiction`
- `test_verify_rejects_bool_in_rep_observation`
- `test_verify_rejects_negative_perf_counter`
- `test_verify_rejects_unknown_or_missing_rep_evidence`
- `test_verify_accepts_zero_perf_counters`

また、`s8b_v2_freeze_fixture.py`、`_FakeScalePoint`、stats の `_sess`、ratified fixture の session/result helper を変更しているため、それらを共有する consumer test 全体へ波及する。

### 静的検査

以下を実施した。

- 変更 11 ファイルの `python3 -m py_compile`
- 変更 11 ファイルの `ast.parse`
- production の必須引数、exact-int、非負判定の AST 検査
- positive control が `[100, 100, 101, 103, 103]`、既定 closure、実 `measure_point`、fake subprocess の構成であることの AST 検査
- pytest 相当の import path を設定した変更 11 module の import
- `git diff --check`
- 変更ファイルの NFC 検査
- no-touch ファイルと `output/` の差分ゼロ確認
- `ALLOWED_EXCLUDED_REASONS`、`_APPROVED_REASONS`、`FORMULA_ID`、`PROTOCOL_SCHEMA`、`MANIFEST_SCHEMA` の固定値確認

pytest と build は一切実行していない。テスト結果の赤・緑は申告しない。**実装済み・未実走**である。docs 編集、commit、Web 検索も行っていない。

### 受理・拒否挙動

変更前は、bench stdout が parse できれば rc 異常や perf event 欠落があっても tps が全件統計へ入り、5 本が有限・正・低 CV なら median が cell に入った。

変更後は、rc 0 かつ perf-required 時の 4 event がすべて非負 exact int の rep だけを `throughputs` へ射影する。1 rep でも違反すれば本数不足となり、session 全体が invalid、median は `None`、cell medians には入らない。raw tps と違反証跡自体は保存される。no-perf pilot は rc 0 と `not_required` なら従来どおり有効で、counter 0 も complete である。

統計式、CV、floor 閾値、4 理由の閉表、protocol pin は変更していない。正常 official、正常 no-perf、counter 0、測定前 v2 resume、非 floor `measure_point` caller は過剰拒否しない。指示外の受理集合拡大はない。PATH による perf 選択と competing 自己申告の残余は裁定どおり scope 外である。

### 所有外 caller と未達事項

静的 call-site 検査で、production の明示済み caller は floor campaign 2 件と ratified verifier 1 件だった。一方、no-touch の [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_holdout_freeze.py:1359) に、`expected_use_perf` を渡さない旧 caller が 1 件残る。

これは「引数を署名上必須にする」と「generator pin 対象を 1 byte も触らない」を同時には満たせない境界である。現状、この旧 v2 candidate generator が当該 call まで到達すると `TypeError` になる可能性がある。影響候補は `test_s8b_holdout_freeze.py` の v2 candidate build/generate 系 consumer 群である。

親は受入実走前に、次のいずれかを裁定する必要がある。

- pinned generator に限った official-only 互換例外を正式に認める。
- generator pin と再 seal を伴う人間手番として、caller に `expected_use_perf=True` を追加する。

私は no-touch 違反を避けるため、この caller は変更していない。これ以外に静的に確認できた未達項目はない。