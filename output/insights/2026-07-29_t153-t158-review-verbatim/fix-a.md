A 担当 fix を完了しました。docs 編集・commit・stage 操作は行っておらず、段 5 の stage 済み状態を保持しています。

### 所見対応

| 所見 | 状態 | 対応 |
|---|---|---|
| R1-1 | closed | `has_target=bool(_positional_tokens(args))` 化。値 option と `--deselect=` を target に数えない |
| R1-2 | closed | positional は空、または `_DEFAULT_TARGET` と完全一致する場合のみ acceptance |
| R1-3 | closed | `PYTEST_ADDOPTS`、shlex 失敗、no-execution、未知の合成 short option を処理 |
| R1-4 | closed（A側） | regular・非 symlink marker と非 symlink `.git` を必須化 |
| R1-5 | partial | B 所有の startup handoff 検査。A 側変更なし |
| R1-6 | closed | final で git 実行不能・非 0・decode 不能を rc=13 |
| R1-7 | partial（裁定どおり） | GIT allowlist と prompt=0 を実装。PATH/HOME 防御は refuted のため未実装 |
| R1-8 | partial | B 所有の output checker。A 側変更なし |
| R1-9 | closed（A側） | GIT 4 変数の毒注入テストへ強化 |
| R1-10 | partial | B 所有の output checker test。A 側変更なし |
| R1-11 | closed | repo 外 cwd からの plain relative target を追加 |
| R1-12 | closed（A側） | deletion/submodule の `UnicodeDecodeError` を所定 rc へ変換 |
| R1-13 | partial | cache・失敗・timeout 分岐を単体検証。実地 auto-init 成功は主張しない |
| R2-1 | closed | local modules cache がある場合だけ init |
| R2-2 | closed | rev-parse/cache 不成立時は init せず、init は timeout=120 |
| R2-3 | closed | 個別 file/node を targeted 化 |
| R2-4 | closed | `PYTEST_ADDOPTS` と合成 short option を acceptance から除外 |
| R2-9 | closed | deletion rc=13、submodule rc=14 |
| regressed | なし | 既存の targeted 警告続行、no-execution skip、非 final git fail-open を維持 |

### 変更箇所

- [tools/run_tests.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/tools/run_tests.py:337): positional/acceptance、GIT env、rc=13/14、submodule cache/init
- [test_run_tests_preflight.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_preflight.py:132): acceptance、毒注入、final、submodule、V12 回帰
- [test_run_tests_task_run.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_task_run.py:50): 記録経路の `cwd=_REPO`
- [test_run_tests_nproc.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_nproc.py:161): 非記録経路の `cwd=_REPO`

### 実行 nodeid・結果

- `orchestrator/tests/test_run_tests_preflight.py` — 64 passed
- `orchestrator/tests/test_run_tests_task_run.py` — 44 passed
- `orchestrator/tests/test_run_tests_nproc.py` — 13 passed
- `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` — 1 passed
- 合同指定実行 — 121 passed
- `tools/check_codex_agents.py` — OK
- `tools/check_docs.py` — 違反なし
- `git diff --check` — 問題なし

### 波及静的列挙

- `tools/run_tests.py` の各 preflight と `main()` が直接 consumer。
- `tools/dev_waves/cli.py` は runner の非 0 を一般処理しており、旧 rc=3/4 の数値依存なし。
- task-run 記録は preflight 通過後のみで、rc=13/14 の台帳混入なし。
- `check_wave_startup.py` は別実装・B 所有のため未変更。
- 指定外ファイル、docs、conftest、README allowlist への変更なし。

### 変異 kill 対応

| 変異 | kill nodeid |
|---|---|
| V1 | `test_main_deletion_preflight_failure_is_wired_before_xdist` |
| V2 | `test_main_submodule_preflight_failure_is_wired_before_xdist` |
| V3 | `test_sidecar_setup_and_record_failures_preserve_rc_and_output` |
| V4 | `test_opt_out_preserves_exact_command_and_call_shape`、nproc の main call-shape test |
| V5 | `test_main_assembles_absolute_relative_target_from_other_cwd` |
| V10 | `test_unstaged_deletion_gate_detects_count_and_scrubs_git_env` |
| V12 | `test_main_absolutizes_plain_relative_target_from_other_cwd` |
| P1 | `test_targeted_run_does_not_invoke_deletion_gate` |
| P2 | `test_targeted_missing_submodule_warns_without_init` |

## 総括

**GO（Author A 担当範囲）。期待赤・実赤ともになし。121 + 1 tests passed、regression なし。**