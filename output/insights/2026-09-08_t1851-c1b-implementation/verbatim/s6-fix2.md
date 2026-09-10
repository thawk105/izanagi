## 総括

| 所見 | 状態 | 対応 |
|---|---|---|
| S-1 | closed | pre-output evidence を canonical bytes の create-only file として保存し、発行時・replay 時に同じ validator で probe、capture failure、launch failure の digest を再導出。[leaf](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/campaign/s8b_terminal_evidence.py:491)、[保存処理](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/campaign/s8b_attempt_registry.py:2735)、[replay](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/campaign/s8b_attempt_registry.py:1498) |
| S-2 | closed | rep sink を一度 `dict` 化した直後に integrity を導出し、その結果を snapshot に封印。campaign record も同じ一回取得済み dict を canonical 化前に型検査。[rep snapshot](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/campaign/s8b_terminal_evidence.py:604)、[campaign snapshot](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/campaign/s8b_terminal_evidence.py:699)、[負例](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/tests/test_s8b_terminal_evidence.py:674) |
| S-3 | closed | F1'・F3' を accept-only recorder に変更し、mutant では偽 draft が recorder まで到達する形へ修正。[recorder](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/tests/test_s8b_floor_attempt_launcher.py:204)、[F1'](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/tests/test_s8b_floor_attempt_launcher.py:1726)、[F3'](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/tests/test_s8b_floor_attempt_launcher.py:1858) |
| S-4 | closed | F2' を builder-exposed rep metadata の遅延 snapshot／再読へ再照準。mutant で偽 draft が accept-only recorder まで到達。probe 非共有 assertion は構造検査としてのみ維持。[F2'](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/tests/test_s8b_floor_attempt_launcher.py:1814) |

S-1 は「external evidence の create-only file」案を採用しました。保存先は `floor-attempt-registry-receipts/external-evidence/<sha256>.json` です。[発行時照合](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/campaign/s8b_attempt_registry.py:3246)と [replay 照合](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/campaign/s8b_attempt_registry.py:1560)は同じ検査を使用します。攻撃再現の発行・replay 負例も追加しました。[tests](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2/orchestrator/tests/test_s8b_attempt_registry.py:4010)

R-1・R-2・R-4・R-5・R-6・R-7・R-8 の既存 closed 7 件は維持されています。F1'、F3'、F4〜F7 の局所変異を再実測し、各対象 test が期待どおり赤になりました。R-3 は S-1 により closed へ進みました。v1 関連 production file は無変更で、terminal exact 24 key、空の retryable reason 集合、既定 `retryable_reason_field="failure_reason"` を core/profile harness で確認しています。

変異の単一帰属確認結果:

- F1'、F2'、F3': 対応 gate を外すと偽 draft が accept-only recorder へ到達。
- F4: 3 identity の発行・replay 計6負例だけが赤。
- F5: capture/count の直接正負対だけが赤。
- F6: helper 直呼び4例だけが赤。v1 側の具体名は維持。
- F7: origin gate を外すと real terminal publish へ到達。
- F8: registry 全147件中、replay 改竄負例1件だけが赤。
- F9: leaf 全72件中、`int` subclass、`IntEnum`、`str` subclass の負例5件だけが赤。
- 確認できなかった変異: なし。

実走結果はすべて自走 harness、全 file nodeid `::<all>` です。

- 所有5 harness: 407 passed
  - `test_s8b_terminal_evidence.py`: 72
  - `test_attempt_registry_core_s8b_profile.py`: 111
  - `test_attempt_registry_core_equivalence.py`: 16
  - `test_s8b_attempt_registry.py`: 147
  - `test_s8b_floor_attempt_launcher.py`: 61
- consumer 7 harness: 809 passed
  - `test_trial_registry.py`: 240
  - `test_p3_autonomous_workload_trial.py`: 266
  - `test_s8b_holdout_admission.py`: 175
  - `test_s8c_acceptance_receipt_v2.py`: 38
  - `test_ccbench_spawn_sites.py`: 44
  - `test_s8b_scheduler_accounting.py`: 39
  - `test_official_perf_closure.py`: 7
- `git diff --check`、production `py_compile`: 緑
- 合計: 1216 passed

所有外への変更はありません。docs 編集・commit とも行っていません。変更は所有内6 fileのみです。

- production: `+306 / -40`
- tests: `+181 / -32`
- 合計: `+487 / -72`