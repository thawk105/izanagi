C1b 統合層 4.1〜4.4 を実装しました。docs・leaf は変更せず、commit も作成していません。

主な実装:

- [attempt_registry_core.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/orchestrator/campaign/attempt_registry_core.py:198)
  - `retryable_reason_field` を追加。
  - terminal/retryable 両枝と observed/not-consumed の null matrix を更新。
  - v2 専用 terminal field を keyword-only で追加し、v1 への非 null 入力を拒否。
- [s8b_attempt_profile.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/orchestrator/campaign/s8b_attempt_profile.py:492)
  - v2 terminal だけに 2 key を追加。
  - E2 exact 4 語を設定。
  - sealed evidence と terminal 行の 11 項目を全件照合。
- [s8b_floor_attempt_launcher.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/orchestrator/campaign/s8b_floor_attempt_launcher.py:534)
  - v2 policy、durable identity、binary digest、monotonic duration、capture snapshot を保持。
  - `TimeoutExpired` を v2 のみ `subprocess.TimeoutExpired` に正規化。
  - draft 発行後、production wrapper だけが固定 adapter を呼ぶ構成に変更。
- [s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/orchestrator/campaign/s8b_attempt_registry.py:1128)
  - draft の 12-key capability への昇格、create-only evidence 公開、no-follow reader、durable claim 再照合を実装。
  - terminal を含みうる replay 8 箇所を中央 loader に統合。
  - old/candidate replay の双方で evidence を独立再読。
  - 旧 v2 terminal API の拒否と v1 adapter API は維持。

## 総括

- 実装状況:
  - 4.1 core: 完了
  - 4.2 profile: 完了
  - 4.3 launcher: 完了
  - 4.4 adapter: 完了

- 所有対象と leaf の実走:
  - `test_attempt_registry_core_s8b_profile.py`: 111 passed
  - `test_attempt_registry_core_equivalence.py`: 16 passed
  - `test_s8b_attempt_registry.py`: 136 passed
  - `test_s8b_floor_attempt_launcher.py`: 47 passed
  - `test_s8b_terminal_evidence.py`: 65 passed
  - 合計 375 件、赤なし

- consumer/共有 fixture 実走:
  - `test_trial_registry.py`: 240 passed
  - `test_p3_autonomous_workload_trial.py`: 266 passed
  - `test_s8b_holdout_admission.py`: 175 passed
  - `test_s8c_acceptance_receipt_v2.py`: 38 passed
  - `test_ccbench_spawn_sites.py`: 44 passed
  - `test_s8b_scheduler_accounting.py`: 39 passed
  - `test_official_perf_closure.py`: 7 passed
  - `test_reflux_formal_consumer.py`、`test_s8b_floor_stats.py`、`test_s8b_floor_campaign.py`、`test_s8c_preregistration_predicates.py` は指定形式で rc=0。ただし自走 harness がなく test node は未実走。
  - `IZANAGI_RUN_GROWTH_HELD_TESTS` は設定していません。

- 呼出し閉包の実測:
  - `_atomic_update_locked`: 2 caller
  - `_atomic_update`: 7 caller
  - `_atomic_update_with_consumption_marker`: 2 caller
  - transition callable: production 7 + test 4 = 11
  - core `record_attempt_terminal`: production 4 + test 6 = 10 direct/function-value caller
  - `record_attempt_terminal` identifier の consumer 閉包: 14 file

- 変異照準:
  - S1: 下層直呼びで kill 確認。[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2283)
  - S2: old `(0 terminal, overrideなし)`、candidate `(1 terminal, overrideあり)` の2回を確認。[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/orchestrator/tests/test_s8b_attempt_registry.py:3872)
  - `not-consumed`: null 正例と非 null 拒否の対を下層直呼びで確認。[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2319)
  - M1〜M12: すべて単一照準 node で kill 可能と確認。未確認なし。
  - sealed row の 11 項目も上流 gate を避けた profile 直呼びで個別確認。[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/orchestrator/tests/test_s8b_attempt_registry.py:4145)

- 所有外への波及:
  - 実変更が必要な所有外 file はなし。
  - `p3_autonomous_workload_trial.py:4420`、`trial_registry.py:3442/3466`、`s8c_preregistration_evidence.py:1639/1737` は keyword-only 既定値により変更不要。
  - `launch_floor_attempt()` の production caller は引き続き 0 件。実環境値域は主張しません。
  - `s8b_terminal_evidence.py`、docs、campaign/freeze 関連 file は未変更。

- 実体化できなかった契約条項: なし。

- 差分行数:
  - production: `+1040 / -75`
  - test: `+1206 / -23`
  - 現在の対象 file 総行数: production 7,840、test 9,466
  - 指定規模内です。