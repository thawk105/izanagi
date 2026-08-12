## 所見ごとの対応

- F1 — `partial`（実装済み・未実走）  
  fixture consumer の非空、既知 fixture 2 系統の実在、一意性、consumer 数 2 以上を固定しました。空 closure 偽 report の拒否 control も追加しました。  
  [test_real_repo_serialization.py:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:579)  
  [test_real_repo_serialization.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:772)

- F2 — `partial`（実装済み・焦点 pytest 未実走）  
  root 文字列比較を Git common-dir identity 比較へ変更しました。canonical path と `(st_dev, st_ino)` を比較し、pytest 内の解決不能は fail-closed、pytest 外は probe 前に return します。  
  [patchharness.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/patchharness.py:272)  
  [patchharness.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/patchharness.py:315)  
  [test_campaign.py:10216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_campaign.py:10216)

- F3 — `partial`（実装済み・未実走）  
  `source_digest` の show/status/diff と `repo_tree_util` の status/ls-files を、それぞれファイル内の単一 sanitiser に統一しました。paired consumer 経路の env 同一性を検査します。  
  [source_digest.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:597)  
  [source_digest.py:776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:776)  
  [source_digest.py:815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:815)  
  [repo_tree_util.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/repo_tree_util.py:21)

- F4 — `partial`（実装済み・未実走）  
  両 sanitiser と回帰テストの forbidden 集合を `GIT_CEILING_DIRECTORIES` 込みの 7 変数へ強化しました。

## 実装した内容

- `patchharness.py`
  - 衛生化した read-only Git env を追加。
  - `git rev-parse --path-format=absolute --git-common-dir` と inode による repository identity 比較を追加。
  - production の probe コストがゼロである control、実 submodule の `include/` 経由を拒否する control、解決不能の拒否を追加。

- `source_digest.py`
  - `_sanitized_git_env()` を新設。
  - `_git_show()`、`_tracked_status_paths()`、`_tracked_diff_sha256()` の全 Git 呼出しを統一。

- `repo_tree_util.py`
  - `_sanitized_git_env()` を新設。
  - `_repo_status()` と `list_tracked_and_untracked_files()` を統一。

- `test_real_repo_serialization.py`
  - `real_known_axes_doc` と `benchmark_snapshots` の実在・fan-out control を追加。
  - 全 closure が空の偽 report を拒否する control を追加。

- `test_campaign.py`
  - guard の subdirectory、production no-probe、解決不能、別 repository の controls を追加。
  - `resolve_evidence()` の paired status/diff と `_git_show()` が同じ衛生化 env を受ける検査へ強化。

- `test_s8b_protocol_builder.py`
  - status と ls-files の paired env 検査へ強化。

`REAL_REPO_SERIAL_NODES`、禁止された 2 ファイル、docs は変更していません。commit も作成していません。

## 実走結果

焦点 pytest は次の 4 node を同一走行で 2 回投入しましたが、いずれも runner rc=16、`qstat -Q preflight rc=1` で pytest 本体は未実走です。

- `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `orchestrator/tests/test_campaign.py::test_patchharness_real_shared_checkout_guard_is_pytest_only_and_fails_closed`
- `orchestrator/tests/test_campaign.py::test_source_digest_status_scrubs_git_environment_and_disables_optional_locks`
- `orchestrator/tests/test_s8b_protocol_builder.py::test_repo_status_scrubs_git_environment_and_disables_optional_locks`

その他の実走結果:

- `git submodule update --init`: 最終再試行 rc=0
- root と `external/ccbench/include` の read-only common-dir probe: 各 rc=0、同一 common-dir
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `git diff --check`: rc=0

空 closure control を含む一時変異の赤確認は、pytest dispatch 不能のため未実走です。

## 受理・拒否挙動の変更前後

- F1:
  - 変更前: 全 closure が空でも相互検査が成立し、正本閉包を誤受理。
  - 変更後: 導出集合が空、既知 fixture が不在／非一意、consumer が 2 未満なら拒否。

- F2:
  - 変更前: 実 submodule root のみ拒否し、`include/` 等の subdirectory は受理。
  - 変更後: 同じ Git common-dir に属する subdirectory／alias も未登録 node なら拒否。pytest 内の identity 解決不能も拒否。別 repository と登録済み node は受理。pytest 外は従来どおり無条件受理し、Git probe もしません。

- F3:
  - 変更前: 親 Git env により status と diff/show が異なる repository を参照可能。
  - 変更後: 全呼出しが明示された `-C`／`cwd` の repository を参照し、proof 混成を拒止。

- F4:
  - 変更前: `GIT_CEILING_DIRECTORIES` を継承。
  - 変更後: 他の repository 指定変数と同様に除去し、subdirectory caller の偽拒否を防止。

## 波及可能性の静的列挙

- `patchharness.checkout()`:
  `s1_direct_comparison`、`p3_s4_loop*`、`silo_ladder_rung1` と関連 checkout tests。pytest 内では identity probe が追加されます。

- `source_digest.resolve_evidence()`:
  `pipeline`、`loop`、`buildcache`、各 calibration／coverage／floor／profile driver。通常 env の証拠値は不変で、汚染 Git env 下だけ参照 repository が是正されます。

- `repo_tree_util`:
  `test_campaign_import_invariant`、`test_s8b_protocol_builder`、`test_real_repo_serialization`、`test_ruleops`。

- 共有 fixture:
  `test_s1_measurement_freeze.py` の `real_known_axes_doc` と、所有外で編集禁止の `test_codex_reasoning_ab.py` の `benchmark_snapshots`。consumer の増減は collection control に波及します。

## やり残し

- 上記 4 node の計算ノード実走。
- fixture 空 closure 変異が実際に期待 node を赤にする動的確認。
- `test_campaign.py`、`test_real_repo_serialization.py`、`test_s8b_protocol_builder.py` の変更ファイル単独走と関連回帰。
- 親による変異 matrix、受入全走、commit。  
  dev-wave 実装子契約に従い、未実走のため F1〜F4 を `closed` とはしていません。

## 総括

F1〜F4 のコードと controls は許可された 6 ファイルへ実装済みです。静的検査と read-only repository identity probe は成功しましたが、pytest は dispatch infrastructure failure（rc=16）で未実走のため、全所見を `partial` として親へ返します。