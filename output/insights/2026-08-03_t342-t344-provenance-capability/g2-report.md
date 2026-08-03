G2 の修正を working tree に残しました。docs・commit・git add・branch 操作は行っていません。静的コンパイルは成功しましたが、`pegasus02` login-node 規律により pytest は未実行です。

### 対応表

| 対象 | 状態 | 対応 |
|---|---|---|
| レビュー1 所見5: critic reflux-on | closed（未実測） | validated view を入口で一度発行し、全 loader で共有。main/sort/red の raw 呼出しも除去 |
| レビュー1 所見7 / レビュー2 所見1: guided/autonomous | partial | autonomous は closed。guided の identity API は修正したが、後述の replay-only WAL topology が残存 |
| レビュー2 所見2: diff-reject topology | closed（未実測） | START/ABORT に同一 `build_attempt_id`、実 policy-bound fixture、exact payload 検査 |
| レビュー2 所見6: Layer3 自己照合 | closed（未実測） | artifact validator の独立 decision と照合し、独立 literal＋全 field 単独変異を追加 |
| `test_guided.py::test_cmd_evaluate_repairs_committed_tail_before_four_new_frames` | closed（未実測） | policy keyword を追加 |
| `test_guided.py::test_cmd_start_atomic_loser_is_structured_and_touches_no_meta_or_wal` | closed（未実測） | 同一 no-build policy で identity 確立 |
| `test_guided.py::test_cmd_start_acquires_lock_before_winner_writes_meta` | closed（未実測） | policy-bound config と API 引数を整合 |
| `test_p3_s4_loop.py::test_comment_reject_wal_to_critic_digest_does_not_repeat_payload` | closed（未実測） | 現行 payload と attempt ID 一致を固定 |
| `test_autonomous_trial_completeness.py::test_campaign_identity_is_pinned_without_producer_helper_oracle` | closed（未実測） | current build ID と pre-T343 ID を分離 |
| `test_p3_exploration_namespace.py::test_main_public_entry_routes_runtime_layout_and_selector[red]` | closed（未実測） | red driver に validated view、fixture に実 lock/WAL を追加 |

regressed と判定した項目はありません。

### 通常経路の根拠

Guided の identity 配線は、共有 no-build policy の生成・config 束縛・start/evaluate への同一 policy 引渡しを行っています。

- [guided.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/campaign/guided.py:48)
- [guided.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/campaign/guided.py:97)
- [guided.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/campaign/guided.py:159)
- 対応テスト: `test_cmd_start_acquires_lock_before_winner_writes_meta`、`test_cmd_start_atomic_loser_is_structured_and_touches_no_meta_or_wal`、`test_cmd_evaluate_repairs_committed_tail_before_four_new_frames`
- pre-policy lock 非書換え: [test_guided.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/tests/test_guided.py:343)

ただし、実 `_print_state()` まで含む guided 通常経路は未閉鎖です。新 lock は post-policy なのに `_log_eval()` が receipt・attempt ID なしの `BUILD_START→COMMIT` を書くため、所有外 `artifact_admission.py` の topology validator と衝突します。identity API の受入3件は直していますが、guided E2E が動くとは主張しません。

Autonomous は no-build/build 双方で共有 context を保持し、build では parser-issued authority を必須化しました。

- policy-bound campaign: [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/campaign/p3_autonomous_workload_trial.py:501)
- no-build を含む共有 context: [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/campaign/p3_autonomous_workload_trial.py:1225)
- public build authority: [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/campaign/p3_autonomous_workload_trial.py:1518)
- CLI authority: [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/campaign/p3_autonomous_workload_trial.py:1698)
- テスト: `test_no_build_campaign_identity_binds_shared_policy_context`、`test_run_trial_other_build_requires_parser_authority_before_artifact`、`test_run_trial_build_public_entry_passes_exploration_layout_to_trigger`

### 変更した既存期待値

- diff-reject payload に `build_attempt_id` を追加し、START/ABORT の値一致を検査。
  - 歴史値: `_PRE_T343_DIFF_REJECT_START_KEYS` / `_PRE_T343_DIFF_REJECT_ABORT_KEYS`
  - 現行値: `_T343_DIFF_REJECT_*`
  - [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/tests/test_p3_s4_loop.py:68)

- trigger campaign ID:
  - pre-T343: `3f72ecd5` / `75727902`
  - current: `0e79a5f1` / `63bc09ae`
  - [test_p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:89)

- autonomous campaign ID:
  - pre-T343 no-build: `948f4c43`
  - current policy-bound: `623e929a`
  - 両集合を別定数で保存: [test_autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g2/orchestrator/tests/test_autonomous_trial_completeness.py:77)

### 検査

実行済み:

- 所有 production/test 16ファイルの `python3 -m py_compile`: rc=0
- `git diff --check`: rc=0

pytest nodeid は0件です。`hostname=pegasus02` であり、AGENTS.md が login-node 上の pytest を単一 nodeid も含め禁止しているためです。したがって緑は主張しません。

未実行:

- 所有 test file の pytest 全て
- 受入全走
- mutation
- build・campaign 実走
- 所有外テスト

### 直さず報告した項目

- guided replay-only WAL と post-policy attempt topology の不整合。正直に閉じるには、登録済み replay/no-build receipt または no-build 専用 topology 契約が必要です。`artifact_admission.py` / `build_admission.py` は所有外のため変更していません。
- 受入18件中、G2外の12件は未対応です。
- レビュー2の machine sweep、T126、silo ladder、mutation attribution、およびレビュー1の overlay関連所見は所有外として未変更です。
- 既存の他単位差分には触れていません。

## 総括

1. critic は raw layout を直接 loader に渡さず、同一 validated view を green/red 全経路で共有する形に統一しました。
2. autonomous の generator ID は権限として扱わず、build は parser-issued coder authority を明示必須にしました。no-build も identity 用 context を保持します。
3. Layer3 decision は fresh Layer3 自己照合だけに依存せず、独立 artifact decision と照合し、receipt 全 field の単独変異を固定しました。

残存する重要事項は guided の replay-only WAL topology です。また pytest 未実行のため、G2の元6赤は「修正済み・未再測定」、G2外12赤はそのままです。