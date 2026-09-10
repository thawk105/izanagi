## 総括

実装は所有された新規 2 ファイルに限定しました。docs 編集・commit・既存挙動への import 配線はありません。

- 実装: [s8b_terminal_evidence.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-leaf/orchestrator/campaign/s8b_terminal_evidence.py:530)
  - `TerminalEvidenceProjection`
  - `SealedTerminalEvidenceDraft`
  - `ValidatedTerminalEvidence`
  - `derive_terminal_projection(document)`
  - `seal_terminal_evidence(reservation, opened, terminal)`
  - `require_sealed_terminal_evidence(value)`
- Test: [test_s8b_terminal_evidence.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-leaf/orchestrator/tests/test_s8b_terminal_evidence.py:420)

実走結果:

- `test_s8b_terminal_evidence.py::*`: 緑、65 passed
- `test_official_perf_closure.py::*`: 緑、7 passed
- `test_pytest_collection_config.py::*`: 緑、76 passed
- `test_campaign_import_invariant.py::*`: 28 passed、2 failed
  - 赤は既存・所有外の6 pathに限定され、新規 leaf は違反一覧にありません。
  - 該当: `condition_meaning_gate.py`、`floor_pair_driver.py`、`paper_story_a2_certification.py`、`sort_swo_oracle.py`、`test_layer3_report.py`、`tools/pegasus/a5_second_boot_backoff_sweep.sh`
- 構文、whitespace、U+0300〜U+036F 検査: 緑

L1〜L18はすべて単一理由で殺せることを確認しました。L4/L5は別パラメータ、L8〜L11は下層実体への直接検査、L13は捕捉3語の正例と集合外の負例、L15は厳密型、L18は内部 bytes 非公開性を個別に検査しています。未確認の変異はありません。

所有外への静的波及候補:

- 統合本体: `attempt_registry_core.py`、`s8b_attempt_profile.py`、`s8b_attempt_registry.py`、`s8b_floor_attempt_launcher.py`
- caller/API 閉包: `s8b_floor_campaign.py`、`p3_autonomous_workload_trial.py`、`trial_registry.py`、`s8c_preregistration_evidence.py`
- consumer tests: core profile/equivalence、attempt registry、launcher、floor campaign、ratified freeze/verify
- 共有 fixture: `s8b_floor_evidence_fixture.py` とその floor stats/materialization/freeze/admission 系 consumer
- 現行 launcher の `type(failure).__name__` は `TimeoutExpired` を生成する一方、契約語は `subprocess.TimeoutExpired` です。統合子では [s8b_floor_attempt_launcher.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-leaf/orchestrator/campaign/s8b_floor_attempt_launcher.py:408) の v2 発行側正規化が必要です。
- 現行 reservation には leaf が要求する durable `schedule_row_sha256`、`records`、`threads`、`workload` が未搭載です。これは plan §4 の統合子側変更です。

契約 v3.1 / plan §3 の leaf 条項で実体化できなかったものはありません。draft 昇格、durable row/file 全件照合、writer 配線は指定どおり統合子の範囲として未実装です。

行数:

- production: 873 行
- test: 692 行