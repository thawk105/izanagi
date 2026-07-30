実装は author worker 所有の4ファイルだけに限定しました。commit、docs、handoff、insight、Skill、dispatcher、`.gitignore` は変更していません。

### 実装内容

- [tools/dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py)

  - linked `.git` → common admin → `gitdir` backpointer → primary `.git` を bytes/dirfd/inode で双方向検査。
  - valid handoff 3状態・stale、登録済み Claude/Codex direct-child worktreeだけをmain untracked例外化。
  - shallow/graft/replace、filter/promisor設定を拒否。
  - hooks、fsmonitor、autostash、maintenance、lazy fetchを無効化。
  - tested A/T、exact `rev-list --reverse A..T`、`A == C` または監査済み `A <= C <= T` を検査。
  - common git-dirのnonblocking flockを使用。merge childにはlock FDだけを限定継承。
  - Git mutationをSHA targetへの `merge --ff-only` 1回に限定。
  - `landed`、`already-landed`、`stale-main`、`lock-busy`、`not-landed`、`landed-postcondition-failed`をJSON/rcで分離。
  - gitlink変更は拒否せずlandするが、D16同期前に成功を偽らず `landed-postcondition-failed` を返す。

- [orchestrator/tests/test_dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py)

  - pytest／直接runner両対応。
  - same-base二waveのwinner→stale loser→再同期→loser land E2E。
  - foreign artifactのbytes/inode不変、unknown untracked拒否。
  - helper SIGKILL後のmerge child lock保持、限定FD継承、Git argv mutation面を実測。

- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py)
- [orchestrator/tests/test_check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py)

  - `DW-O23`、段5/6/9 dispatch、条件23を固定。
  - `DW-S09`の唯一経路literalを固定。
  - helper pathを`DW-S09`／`DW-O23`以外、特にCodex Skillへ重複pinする変更を拒否。
  - aggregate budgetは23,962 / 24,000 bytesのまま。定数を上げていません。

### 実走結果

緑：

- `python3 orchestrator/tests/test_dev_wave_land.py`
  - 全範囲、19 passed。
- `python3 orchestrator/tests/test_check_docs.py`
  - 全範囲、136 passed。
- `python3 tools/run_tests.py -q orchestrator/tests/test_dev_wave_land.py orchestrator/tests/test_check_docs.py orchestrator/tests/test_plain_runner_coverage.py`
  - 指定3ファイル範囲、158 passed。
- meta-test `orchestrator/tests/test_plain_runner_coverage.py`
  - 直接runner 3 passed。上記158件にも含まれる。
- 重点nodeid：
  - `test_git_operation_surface_is_read_only_except_sha_ff_merge`
  - `test_merge_child_inherits_only_explicit_lock_not_other_parent_fd`
  - `test_merge_child_inherits_lock_fd_if_helper_is_killed`
  - `test_same_base_two_wave_winner_stale_resync_loser_land_e2e`
  - `test_gitlink_change_lands_but_cannot_report_success_before_d16_sync`
- `python3 tools/check_codex_agents.py`：OK。
- `py_compile`、`git diff --check`：緑。

意図的な赤：

- `python3 tools/check_docs.py`：rc=1、親docs未統合に由来するexact 6 findingsのみ。
  - `DW-O23` H2欠落
  - 段5・6・9のO23 dispatch欠落
  - 条件23欠落
  - `DW-S09`唯一経路literal欠落

親の全走、mutation matrix、受入全走を代替したとは主張しません。

### 受理・拒否と波及

新しい受理集合は、schema-validな三状態/stale handoff、双方向登録済みClaude/Codex worktree、監査済みclosure内のmain前進です。未知untracked、tracked/index/submodule dirt、malformed/nonregular/symlink handoff、admin alias、history modifier、filter/promisor、moved tip、監査列不一致は拒否します。

既存startup/supervisor helperは変更していません。新helperの未結線callerは親所有の共通dispatcherです。`tools/run_tests.py`とplain-runner meta-testは新テストを自動収集します。

既知限界は、協調manager間の事故防止に限定されること、同一UIDの悪意あるGit admin改変・非協調writer・cross-hostでflock非整合なmountを防護しないこと、tested SHA列は受入証明ではないことです。

## 総括

変更ファイルは指定された4ファイルのみ、commitなしです。author検査は19 direct／136 direct／158 repository runnerで緑。親は、予算を増やさず文書を縮約し、`DW-O23`、段5/6/9 dispatch、条件23、`DW-S09`内のexact literal「`tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路」を統合してください。Codex Skillやdispatcher本文へhelper pathを重複記載してはいけません。