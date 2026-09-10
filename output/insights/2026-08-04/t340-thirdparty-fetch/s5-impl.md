現行の受理・拒否挙動は、凍結 submitter が「実 directory・HEAD==policy pin・tracked/untracked clean」を受理し、欠落・symlink・HEAD 不一致・dirty を拒否するものです。origin、repo root、ignored artifact、危険 Git metadata/config は現行判定外です。既存 clone は更新しません。

実装 scope は任意の operator preflight helper に限定しました。凍結 submitter・receipt・proof chain には接続していないため、campaign の受理集合は変わりません。

- [fetch_third_party.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:50)
  - `fetch` / `hydrate` / `verify` / `verify-deps`
  - 明示 cache root、repo 配下拒否
  - `third_party_policy()` 再利用と一時的 `sys.path`
  - hardened Git 環境、危険 config の Git 起動前検査
  - shallow、alternates、promisor、replace、grafts、git-file、sparse、index bit 拒否
  - hydrate は `clone --no-hardlinks --no-checkout` と detached checkout
  - publish は `mkdir` 排他予約後の `os.rename`
  - 成功時 JSON 1 行、失敗時 stderr 1 行、rc=1/2
- [test_pegasus_thirdparty_fetch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:193)
  - local Git fixture のみ
  - HTTPS URL を global `insteadOf` で `file://` に置換し、protocol allowlist で network を構造的に遮断
  - `_run()` / `__main__` harness あり

変異対応は以下です。

| 変異 | 赤になるテスト |
|---|---|
| M1 | `test_m01_policy_cmake_drift_is_rejected_before_acquisition` |
| M2 | `test_m02_hydrate_fresh_clone_excludes_ignored_cache_artifact` |
| M3 | `test_m03_shallow_cache_is_rejected` |
| M4 | `test_m04_alternates_cache_is_rejected` |
| M5 | `test_m05_replace_refs_are_rejected` |
| M6 | `test_m06_untracked_dirty_requires_explicit_all_mode` |
| M7 | `test_m07_head_mismatch_is_rejected` |
| M8 | `test_m08_origin_url_substitution_is_rejected` |
| M9 | `test_m09_final_component_symlink_is_rejected` |
| M10 | `test_m10_publish_reservation_never_replaces_existing_empty_directory` |
| M11 | `test_m11_existing_cache_never_runs_clone_fetch_pull_or_checkout` |
| M12 | `test_m12_git_environment_ignores_host_global_config_and_askpass` |
| M13 | `test_m13_cache_root_inside_repo_is_rejected` |
| M14 | `test_m14_dangerous_cache_config_keys_are_rejected_before_git` |
| M15 | `test_m15_publish_is_reverified_before_success` |

検査結果:

- `py_compile`、`git diff --check`、`check_codex_agents.py`、`check_docs.py`: 成功
- pytest 要求範囲:
  - 新規テスト全体
  - 新規テスト全体 + `test_plain_runner_coverage.py`
- 3 回とも dispatcher が `qstat -Q preflight rc=1`、rc=16 で停止。pytest 実行 nodeid は 0 件で、緑は主張しません。
- 凍結 4 本の SHA-256 は着手前後で一致。
- 変更は許可された新規 2 ファイルのみ。docs、policy registry、`external/ccbench` は未変更、add/commit なし。

所有外への波及候補は、凍結 submitter の hydrate 配置先、T-139 の `IZANAGI_THIRDPARTY_SOURCE_ROOT`、driver の policy/CMake gate、plain-runner meta-test、policy registry・evidence・runtime-module closed-set test です。共有 fixture の変更はありません。

親 docs 未 land の想定 finding は、runbook の運用手順未記載と、4 subcommand の resource 分類未記録の2点です。それ以外の赤は回帰扱いです。

## 総括

- R1〜R7 を新規 CLI と local-Git テストへ実装した。
- X1〜X5、凍結 4 本、docs、policy registry、CCBench は変更していない。
- 静的検査と repository checker は成功した。
- pytest は scheduler preflight 障害で未実走のため、親による計算ノード再走が必要。