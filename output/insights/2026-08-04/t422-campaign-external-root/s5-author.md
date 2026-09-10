実装は完了しました。ただし PBS dispatch 基盤障害により pytest は未実走のため、緑は主張しません。

### 変更内容

- [layout.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:223)
  - `IZANAGI_EXPLORATION_OUTPUT_ROOT` resolver と process pin/reset を追加。
  - env 経路に絶対 path、`.git` 祖先、symlink/non-directory component、euid 所有検査を追加。
  - `ExplorationCampaignLayout.ensure()` に `.claude/worktrees` / `.codex/worktrees` gate を追加。
  - official layout、`repo_output_root()`、`ensure_exploration_namespace()` 本体は不変。

- [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1588)
  - `--run-root` 省略時を env base に接続。
  - materialization 直前に同じ worktree-container gate を追加。

- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3612)
  - env 優先順位・official 非干渉、不正値、pin drift、8c root/gate の4テストを追加。

- [test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2685)
  - fake evaluator の最小 campaign 完走による F98 正例。
  - Claude/Codex worktree-container の作成前拒否。
  - plain untracked file の RC_DIRT 対照を追加。

- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/conftest.py:125)
  - env 削除と両 module identity の pin reset を行う autouse fixture を追加。

差分は5ファイル、490行追加・2行削除です。docs、hooks、land、durable-root、commit/indexには触れていません。

### 検査結果

通過:

- `git diff --check`
- 対象5ファイルの `python3.10 -m py_compile`
- `python3.10 tools/check_codex_agents.py`
- `python3.10 tools/check_docs.py`
- F42 meta-test 検索: 今回のテスト名・件数を固定する該当 meta-test なし

次の7 nodeidを `tools/run_tests.py` で2回 dispatch しましたが、いずれもテスト開始前に `qstat -Q preflight rc=1`、wrapper rc=16でした。

- `test_campaign.py::test_exploration_output_root_env_precedence_and_official_isolation`
- `test_campaign.py::test_exploration_output_root_env_rejects_unsafe_values`
- `test_campaign.py::test_exploration_output_root_env_process_pin_rejects_drift`
- `test_campaign.py::test_autonomous_trial_env_run_root_and_worktree_container_gate`
- `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean`
- `test_dev_wave_land.py::test_exploration_default_root_stops_before_wave_dirt`
- `test_dev_wave_land.py::test_verify_wave_clean_rejects_plain_untracked_file_as_dirt`

直接確認した `qstat -Q` は `Can't create socket (errno: 1)` でした。pytest の失敗や submodule index-lock 偽赤は観測しておらず、pytest 自体が未起動です。

### 受理・拒否集合

変更前は env を無視し、exploration と8cは repo-local既定へ materializeできました。

変更後:

- 非空の明示 `output_root` は従来どおり最優先で、その文字列を無変更で受理。
- env 未設定時は従来の `repo_output_root()` 文字列を無変更で使用。
- env root は安全検査後に canonical 化して受理・process pin。
- 空、相対、`.git` 祖先配下、既存 symlink/non-directory component、他 euid 所有 base、process driftを拒否。
- worktree-container 内は factoryでは受理するが、`ensure()` / 8c materialization直前に拒否。
- main checkout の通常既定、official campaign、sweep、env scopeは不変。
- 8cの明示 `--run-root` は従来どおり優先するが、container gateだけ新たに適用。

### 静的な波及先

production caller は `loop.py`、`p3_kickoff.py`、`p3_s4_loop*.py`、`p3_s4_red.py`、`p3_autonomous_workload_trial.py`、`s8b_oracle_exploration.py`。consumer test は `test_p3_exploration_namespace.py`、各 `test_p3_s4_loop*.py`、`test_p3_autonomous_workload_trial.py`、`test_s8b_oracle_artifacts.py`、`test_s8b_oracle_report.py`です。

共有 fixture は親 env 漏洩を除去し、`campaign.layout` と `orchestrator.campaign.layout` の双方を隔離します。

## 総括

plan v2 のコード・テスト実装は指定所有範囲内で完了しました。静的検査は全通過、pytest はPBS socket基盤障害による未実走で、実装由来の赤は確認されていません。親環境で上記7 nodeidと関連 consumer testの再走が必要です。