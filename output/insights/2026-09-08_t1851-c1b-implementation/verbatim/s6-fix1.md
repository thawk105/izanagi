R-1〜R-8 をすべて実装し、最終実走は全対象で緑です。docs・所有外 file・commit は変更していません。

## 総括

| 項目 | 状態 | 対応 |
|---|---|---|
| R-1 | closed | launcher-origin capability を reserve state と handle fingerprint に束縛し、発行時に再照合。[registry](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix1/orchestrator/campaign/s8b_attempt_registry.py:78) |
| R-2 | closed | protocol と perf receipt を副作用前の canonical snapshot に固定。sealer の reservation 再読なし |
| R-3 | closed | probe・failure・launch failures・rep sink を builder 非共有 snapshot 化し、classification receipt の external digest と再照合。[registry](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix1/orchestrator/campaign/s8b_attempt_registry.py:3168) |
| R-4 | closed | campaign record を builder 直後に一度だけ strict canonical snapshot 化し、launcher と sealer で共有 |
| R-5 | closed | holdout、configuration、retry ordinal を実 slot へ再束縛。[registry](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix1/orchestrator/campaign/s8b_attempt_registry.py:1358) |
| R-6 | closed | capture failure と非ゼロ launch count の矛盾を拒否。[leaf](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix1/orchestrator/campaign/s8b_terminal_evidence.py:736) |
| R-7 | closed | v2 の TimeoutExpired → OSError → RuntimeError 順の基底名正規化。v1 の具体名は維持。[launcher](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix1/orchestrator/campaign/s8b_floor_attempt_launcher.py:431) |
| R-8 | closed | ScalePoint 座標検査を capture 実行済み・failure 無しへ限定し、certified pre-probe competing terminal を実発行。[launcher](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix1/orchestrator/campaign/s8b_floor_attempt_launcher.py:990) |

snapshot 対象は protocol、perf receipt、reservation binding/identity、probe 前後、failure、launch failures、rep sink、measurement throughputs、external evidence digest、terminal scalar、raw bytes、campaign record です。builder には canonical bytes から復元した別 tree を渡します。`seal_terminal_evidence(reservation, opened, terminal)` の公開 signature は変更していません。

最終実走:

- 所有 test 全範囲 `::*`: 400 passed
  - `test_s8b_terminal_evidence.py`: 67
  - `test_attempt_registry_core_s8b_profile.py`: 111
  - `test_attempt_registry_core_equivalence.py`: 16
  - `test_s8b_attempt_registry.py`: 145
  - `test_s8b_floor_attempt_launcher.py`: 61
- consumer:
  - `test_trial_registry.py::*`: 240 passed
  - `test_p3_autonomous_workload_trial.py::*`: 266 passed
  - `test_s8b_holdout_admission.py::*`: 175 passed
  - `test_s8c_acceptance_receipt_v2.py::*`: 38 passed
  - `test_s8b_scheduler_accounting.py::*`: 39 passed
  - `test_ccbench_spawn_sites.py::*`: 44 passed
  - `test_official_perf_closure.py`: 7 passed
- 最終赤: 0
- `test_s8b_floor_stats.py` は module import 依存だが変更 symbol の直接 consumer ではなく、自走 `__main__` が無いため node 実走なし。指定形式での直接起動は rc=0、収集 0
- growth hold は解除していません

F1〜F7 はすべて単一理由で kill できることを確認しました。F1=protocol snapshot、F2=private rep sink 非共有、F3=campaign record 単一 snapshot、F4=3 identity 各独立、F5=capture/count、F6=v2 subclass 正規化、F7=launcher-origin capability。確認不能項目はありません。

所有外への波及:

- 所有外 production caller の変更必要箇所なし。`launch_floor_attempt()` の production caller は引き続き 0 件
- 共有 fixture [test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix1/orchestrator/tests/test_s8b_holdout_admission.py:2001) を real admission/observation 作成に利用したが、変更不要
- `s8b_floor_campaign.py`、stats、holdout、freeze、docs、ledger は未変更
- `git diff --check`、変更 6 file の AST parse、perf semantic inventory、禁止形検索はすべて成功

差分行数:

- production: `+604 / -82`
- test: `+901 / -20`
- 合計: `+1505 / -102`
- commit: なし