段 6 fix を許可された 2 ファイルへ実装しました。R6 訂正を含む F1〜F11 は実装・静的検査上すべて closed です。ただし計算ノード dispatch が 3 回とも rc=16 で停止したため、pytest・変異の実測は未完です。

変更ファイル:

- [fetch_third_party.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:192)
- [test_pegasus_thirdparty_fetch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:226)

主な変更は、Git 起動前の metadata/config 拒否、hydrate 既存先の ignored artifact 拒否、`allow_shallow` の個別化、inode 照合付き publish cleanup、hydrate 専用 `source_root` です。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| C1 | closed | `commondir`、`config.worktree`、`extensions.worktreeConfig` を Git 起動前に拒否 |
| C2 | closed | continuation と旧式 dotted subsection を拒否。odd/even backslash、大小文字・空白を固定 |
| C3 | closed | 既存 hydrate destination に ignored file があれば拒否 |
| C4 | closed | `hardened_metadata=False` を廃止し、deps は shallow のみ許可 |
| C5 | closed | rename 失敗時の同一 inode・空予約 cleanup、publish 後失敗時の rollback |
| C6 | closed | M6 fixture が実 untracked file を作成 |
| C7 | closed | 新規 2 ファイルを `git diff --no-index --check` で個別検査 |
| C8 | closed | sentinel を含む `sys.path` 全体を復元前に比較 |
| D1 | closed | `source_root` は hydrate のみ。ほかの操作では field 自体を省略 |
| D2 | closed | C1/C2 と同じ Git 起動前防壁 |
| D3 | closed | M1/M13 を local-only 化、M6 修正、M12 shape/behavior 分離 |
| D4 | closed | JSON の全 record を fixture の pin/path から独立に exact 比較 |
| D5 | closed | 合法な section 行末コメントと偶数 backslash の正例を追加 |
| F1 | closed | metadata indirection 3 種を pre-Git test で固定 |
| F2 | closed | 自作 continuation 結合を廃止し fail-closed 化 |
| F3 | closed | `reject_ignored=True` を hydrate destination のみに適用 |
| F4 | closed | 訂正 R6 の `source_root` 契約を実装 |
| F5 | closed | gflags/glog でも config・sparse・index bit 等を検査 |
| F6 | closed | 自分の inode 以外を削除しない cleanup と正式 path rollback |
| F7 | closed | `payload.write_text()` で untracked file を生成 |
| F8 | closed | M1/M13 local 化、state-first assert、M12 分割 |
| F9 | closed | `pin`、`head`、`resolved_path` を exact 比較 |
| F10 | closed | 恒真 assert を削除 |
| F11 | closed | `[core] # benign comment` 等の正例を追加 |

### M1〜M15 の単一理由 kill 対応

未実走のため、以下は修正後コードの構造的対応です。

| 変異 | kill を担当するテスト | 単一理由 |
|---|---|---|
| M1 | `test_m01_policy_cmake_drift_is_rejected_before_acquisition` | local acquisition に進まず cache が作られない |
| M2 | `test_m02_hydrate_fresh_clone_excludes_ignored_cache_artifact` | consumer root に ignored poison が存在しない |
| M3 | `test_m03_shallow_cache_is_rejected` | shallow cache の受理 |
| M4 | `test_m04_alternates_cache_is_rejected` | alternates の受理 |
| M5 | `test_m05_replace_refs_are_rejected` | replace refs の受理 |
| M6 | `test_m06_untracked_dirty_requires_explicit_all_mode` | config で隠した実 untracked file の受理 |
| M7 | `test_m07_head_mismatch_is_rejected` | HEAD 不一致の受理 |
| M8 | `test_m08_origin_url_substitution_is_rejected` | origin 差し替えの受理 |
| M9 | `test_m09_final_component_symlink_is_rejected` | symlink source の受理 |
| M10 | `test_m10_publish_reservation_never_replaces_existing_empty_directory` | 既存 destination inode の置換 |
| M11 | `test_m11_existing_cache_never_runs_clone_fetch_pull_or_checkout` | 既存 cache への更新 command 発行 |
| M12 | `test_m12_host_global_insteadof_is_behaviorally_ignored` | host global `insteadOf` が実効化 |
| M13 | `test_m13_cache_root_inside_repo_is_rejected` | repo 内 cache が実際に作成される |
| M14 | `test_m14_dangerous_cache_config_is_rejected_before_git` | 危険 config 後に Git が起動される |
| M15 | `test_m15_publish_is_reverified_before_success` | post-publish 検証を省略し正式 destination が残る |

### 検査結果

- `python3 -m py_compile`：成功
- `python3 tools/check_codex_agents.py`：成功
- `python3 tools/check_docs.py`：成功
- 新規ファイル whitespace：両方とも通常差分を示す rc=1、whitespace 診断 0 件
- pytest 要求範囲:
  - `orchestrator/tests/test_pegasus_thirdparty_fetch.py`
  - `orchestrator/tests/test_plain_runner_coverage.py`
- `tools/run_tests.py` で 3 回 dispatch したが、すべて `qstat -Q preflight rc=1`、rc=16。実行 nodeid は 0 件で、pytest 緑は主張しません
- 変異 M1〜M15：未実走

凍結 4 本は着手前後で SHA-256 が一致し、全 `git hash-object == HEAD` です。`git status` は許可された新規 2 ファイルだけです。docs、policy、CCBench、凍結ファイルは未変更で、add・commit・stash は実行していません。

所有外への波及は、T-139 等の consumer が `.cache_root` ではなく hydrate JSON の `.source_root` を使う必要がある点です。runbook 記録、資源分類、受入・変異再走は親の残作業です。

## 総括

- C1〜C8、D1〜D5、F1〜F11 を実装・静的検査上 closed にした。
- R6 訂正どおり、安全な consumer root は hydrate の `source_root` だけにした。
- 許可された 2 ファイル以外は変更していない。
- 静的検査と repository checker は成功した。
- pytest・変異は scheduler preflight 障害で未実走のため、親の計算ノード再走が必要。