段 6 fix を実装しました。production・docs・index・commit は変更していません。開始時から存在した production 2 ファイルの差分もそのまま保持しています。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| D-01 | partial（実装済み・未実走） | 完全 binding 作成後に disk のみ汚し、live verifier を直接呼ぶ 8-path 負例を追加。対象 path も検査 |
| D-04 | partial（実装済み・未実走） | 正しい記録 blob digest と dirty disk を持つ v2 artifact が `admitted` になる正例を追加 |
| D-06 / L2-01 | partial（実装済み・未実走） | `output/**/campaign.lock` の exact 32-path・全件 v1 census を独立追加。30 campaign mapping は維持 |
| L2-03 | partial（実装済み・未実走） | Layer3 独立 helper を production capture から記録 HEAD blob 経路へ変更 |
| L2-04 | partial（実装済み・未実走） | dirty recorded-blob 正例を 8 path 化し、各 case で独立 `git cat-file` digest と比較 |
| D-08 | partial（実装済み・未実走） | production 定数由来の tuple equality を削除。独立 exact-8 sentinel は維持 |

### 変更箇所

- [test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:119)
  exact-8 sentinel、8-path の直接 live drift 検査、committed mismatch、dirty recorded-blob 正例、production caller census を配置しました。

- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:188)
  evidence 2 lock の golden を追加し、[32-lock census](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:728) と [dirty-disk admission 正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:963) を追加しました。冗長 tuple assertion は削除済みです。

- [test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_layer3_report.py:53)
  同ファイル固有の module namespace を維持したまま、記録 HEAD blob digest から binding を作る helper へ変更しました。

- [campaign_lock_test_support.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/campaign_lock_test_support.py:10)
  共有 v2 fixture は disk 非依存の記録 HEAD blob binding を使用します。

- [test_campaign_lock_codec.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:34)
  閉包サイズ非依存の digest fixtureと、[各 key 欠落・legacy exact-2 拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:166)を保持しています。

### 検査

次を `tools/run_tests.py` で投入しました。

- `orchestrator/tests/test_t671_source_binding.py`
- artifact admission の census、30本 mapping、valid v2、dirty-disk admission の4 nodeid

`qstat -Q` preflight が失敗し rc=16 となったため、pytest 実行件数は 0、passed 件数も 0 です。緑は主張しません。状態は「実装済み・未実走」です。

静的検査として、許可5ファイルの AST parse と `git diff --check` は rc=0 でした。

### 所有外への波及可能性

- production caller は `ident.py` の capture/live/resume 4 call と、`artifact_admission.py` の committed 検証 2 call。変更していません。
- 共有 fixture の consumer は16ファイルです: `test_artifact_admission.py`、`test_autonomous_trial_completeness.py`、`test_campaign.py`、`test_campaign_lock_wal_consumers.py`、`test_critic.py`、`test_p3_autonomous_workload_trial.py`、`test_p3_exploration_namespace.py`、`test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py`、`test_s1_direct_comparison.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`、`test_screening_driver.py`、`test_t126_qualification_artifacts.py`、`test_t671_source_binding.py`。
- decode-only production consumer は `autonomous_trial_completeness.py`、`layer3_report.py`、`wal.py`、`qualification/artifacts.py`。exact-8 wire shape の影響候補ですが未変更です。
- `test_layer3_report.py` は独立 namespace helper のため共有 helperを直接再利用せず、同じ recorded-HEAD 意味論をローカル実装しています。
- 既存 artifact 32 lock は読み取りのみで、bytes は変更していません。

## 総括

- 採用6所見はすべて実装済みですが、rc=16 のため検証状態は全件 partial です。
- pytest は未実走で、緑の主張および残る機能赤の判定はありません。
- AST parse と差分整合検査は通過しました。
- production・docs・git index・commit への変更はありません。
- 波及候補は production caller 2 module、共有 fixture consumer 16 test、decode-only consumer 4 moduleです。