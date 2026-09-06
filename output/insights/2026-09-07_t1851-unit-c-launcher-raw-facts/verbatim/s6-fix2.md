実装を完了しました。[launcher](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix2/orchestrator/campaign/s8b_floor_attempt_launcher.py:175) と [launcher tests](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix2/orchestrator/tests/test_s8b_floor_attempt_launcher.py:807) のみ編集しています。

| 所見 | 判定 | 対応 |
|---|---|---|
| A-1 | closed | 検査時 kwargs の `dict` copy を保持し、capture はその copy のみ使用。pre-probe 中の元 Mapping 変異を検査 |
| A-2 | closed | capture/open failure と `observed` の矛盾を seal 前に拒否。正負両経路を検査 |
| A-3 | closed | 4 helper の正例対照、5 分岐 reason、v2 payload digest、capture failure 差を固定。到達不能な marker callable 検査を削除 |
| A-4 / B-5 | closed | M5 は `reps=3` を維持し、`session_cv_max` 追加だけで digest 不一致を生成 |
| B-1 | closed | `extime=3`、`reps=3`、`use_perf=True` の exact 検査を復元し、私有 list を個別検査 |
| B-2 | closed | fake の私有 sink と公開 list を分離し、実体と同じ 6-key rep record を生成 |
| B-3 | closed | real adapter で reserve、seal、classify、begin observation、terminal まで到達 |
| B-4 | closed | launcher module の依存と probe を差し替え、public API と正式 capability 経由で authority を観測 |
| M4 | closed | public forwarding が別 authority を使う変異を recorder 検査で殺す構成に再照準 |

検査結果:

- 自走 harness: `orchestrator/tests/test_s8b_floor_attempt_launcher.py::*` 全 31 node passed
- 新設 2 node、既存 14 test functionを変更、pytest 展開後は変更 19 node
- `git diff --check`、`py_compile`、`check_codex_agents.py`、`check_docs.py` は green
- pytest wrapper は Pegasus の `qstat -Q` preflight が失敗し、child 未起動の rc=16
- `test_official_perf_closure.py` の既存 fix1 差分は snapshot と完全一致。2 guard 条件の `ast.unparse` 逐語も不変
- `test_ccbench_spawn_sites.py:212` の `_owned_post_probe: 1` pin と単一 spawn siteを静的確認
- adapter、core、profile、campaign、calibrator、docs は未編集。commit も作成していません

## 総括

- 9 所見: closed 9 / partial 0 / regressed 0
- production: `+232/-36`、test: `+520/-41`。双方とも規模上限内
- 新設 2 node / 変更 19 expanded node / launcher 合計 31 node
- 自走 harness: 31 passed
- pytest wrapper: Pegasus qstat infrastructure failure、rc=16、未実走
- 所有外 guard と spawn-site pin: 静的確認済み、不変
