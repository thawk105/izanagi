## 実装した内容

編集は指定された 2 file のみに限定し、docs・commit・remote・submodule 状態は変更していない。

- [tools/codex_reasoning_ab.py:921](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:921)
  - `HEAD`、gitdir、common-dir を `--no-replace-objects` 付きで検査。
  - marker を non-symlink regular file に限定。
  - 期待 admin path の全成分を `lstat` し、symlink admin、rogue marker、common-dir 差し替えを拒否。
  - snapshot では admin の内部 containment を要求し、linked worktree の source では正当な外部 Git admin を許しつつ同一性と symlink-free を検査。
  - 既存理由文字列 3 本は変更していない。

- [tools/codex_reasoning_ab.py:1374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1374)
  - local config key allowlist を実装。
  - seal 後 snapshot は `core.*` の実測 5 key だけを許可。
  - source 初期化時だけ、実測した `branch.*`、`remote.*`、`submodule.*.(url|active)` を追加許可。
  - `submodule.*`、`core.fsmonitor`、`core.autocrlf`、`filter.*`、`include.path` 等の post-seal 混入を拒否。

- [tools/codex_reasoning_ab.py:1466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1466)
  - index と `HEAD^{tree}` を `diff-index --cached --ignore-submodules=none` で照合。
  - tracked path の中間成分 symlink、file type、owner execute bit を検査。
  - regular file と symlink target を Python の raw SHA-1 blob hashで照合。
  - ignored extra file を含む非 directory file-set を完全照合し、nested submodule と `.git` 内部は重複走査しない。
  - `git hash-object`、`git write-tree` は使用していない。

- [tools/codex_reasoning_ab.py:1584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1584)
  - object format と config を、status や内容検査より前に fail-closed で検査。
  - object format は `sha1` のみ受理。

- [tools/codex_reasoning_ab.py:1629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1629)
  - `_submodule_content_identity_reasons(snapshot, repositories)` を追加。
  - inspection failure、snapshot 外 repository を含め、例外ではなく理由 list を返す。

- [tools/codex_reasoning_ab.py:1825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1825)、[tools/codex_reasoning_ab.py:2039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:2039)
  - closure 有効経路と `enforce_closure=False` の両方へ接続。
  - inventory は precomputed 値を再利用。
  - source 初期化では marker/admin/common-dir/config のみ検査し、dirty source の full bytes は拒否しない。

- [tools/codex_reasoning_ab.py:2159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:2159)
  - oracle dict には field を追加していない。

## config allowlist の実測

`/tmp/t1262-config-exact.*` の固定サイズ repo で、次の実 builder 相当手順を実行した。

1. source と snapshot を `git init`。
2. `.gitmodules` と gitlink を commit。
3. snapshot local config に `submodule.child.url` を設定。
4. `git submodule update --init --no-fetch`。
5. child を detached checkout。
6. `_seal_git_object_closure`。
7. 各段階で `git config --local --name-only --list` を採取。

実測 key は次のとおり。

- `git init` 後:
  - `core.repositoryformatversion`
  - `core.filemode`
  - `core.bare`
  - `core.logallrefupdates`

- update 前 root:
  - 上記 4 key
  - `submodule.child.url`

- update・checkout 後 child:
  - 上記 4 key
  - `core.worktree`
  - `remote.origin.url`
  - `remote.origin.fetch`
  - `branch.master.remote`
  - `branch.master.merge`

- seal 後 root:
  - init の 4 keyのみ

- seal 後 child:
  - init の 4 key
  - `core.worktree`

別の `submodule add` / synthetic update probe では `submodule.<name>.active` も観測した。このため source 用 allowlist は dynamic subsection 名を許すが、seal 後 snapshot では dynamic key を一切許可しない。

確定集合は以下。

- seal 後: `core.repositoryformatversion`、`core.filemode`、`core.bare`、`core.logallrefupdates`、`core.worktree`
- source 初期化時のみ追加:
  - `branch.<name>.remote|merge`
  - `remote.<name>.url|fetch`
  - `submodule.<name>.url|active`

現 worktree の `external/ccbench` source config も、この source allowlist で理由なしになることを診断確認した。

## 追加したテスト

以下の nodeid はすべて `orchestrator/tests/test_codex_reasoning_ab.py::` が prefix である。

| 変異 | helper 直呼び node | end-to-end node |
|---|---|---|
| N1 index/HEAD | `test_submodule_content_identity_reasons_rejects_empty_index_and_worktree`、`...rejects_index_entry_absent_from_head_tree` | `test_verify_snapshot_submodule_content_gate_rejects_empty_index_and_worktree`、`...rejects_index_entry_absent_from_head_tree` |
| N2 raw bytes | `...rejects_worktree_blob_mismatch`、`...rejects_crlf_worktree_bytes`、`...rejects_symlink_target_mismatch` | 対応する `test_verify_snapshot_submodule_content_gate_*` 3 node |
| N3 marker/admin | `test_submodule_worktree_state_rejects_marker_bound_to_rogue_admin_dir` | `test_verify_snapshot_submodule_content_gate_rejects_git_marker_bound_to_rogue_admin_dir`、`test_init_submodules_from_local_source_rejects_rogue_source_admin` |
| N4 replace ref | `test_submodule_content_identity_reasons_rejects_replacement_ref_tree` | `test_verify_snapshot_submodule_content_gate_rejects_replacement_ref_without_closure` |
| N5 file-set | `test_submodule_content_identity_reasons_rejects_ignored_extra_file` | `test_verify_snapshot_submodule_content_gate_rejects_ignored_extra_file_without_closure` |
| N6 admin symlink | `test_submodule_worktree_state_rejects_symlinked_expected_admin_path` | `test_verify_snapshot_submodule_content_gate_rejects_symlinked_expected_admin_path` |
| N7 tracked path symlink | `test_submodule_content_identity_reasons_rejects_intermediate_directory_symlink` | `test_verify_snapshot_submodule_content_gate_rejects_intermediate_directory_symlink` |
| N8 config | `...rejects_post_seal_config`、`...rejects_root_local_config`、`...rejects_forbidden_config_key[fsmonitor/autocrlf/filter/include/worktree-config]` | `test_verify_snapshot_submodule_content_gate_rejects_post_seal_config`、`...rejects_root_local_config`、source config 拒否 node |
| N9 closure 無効枝 | ignored extra と replacement ref の `without_closure` node | 同左 |
| N10 再帰 | `test_submodule_content_identity_reasons_rejects_initialized_grandchild_change` | `test_verify_snapshot_submodule_content_gate_rejects_initialized_grandchild_change` |
| N11 mode | `test_submodule_content_identity_reasons_rejects_executable_bit_mismatch` | 対応する verify node |
| N12 object format | `test_submodule_content_identity_reasons_rejects_non_sha1_object_format` | object-format 単独帰属 node |

追加の境界 node:

- `test_submodule_worktree_state_rejects_external_common_dir`
- `test_verify_snapshot_submodule_content_gate_rejects_external_common_dir`
- `test_submodule_content_identity_reasons_returns_reason_for_uninspectable_repo`
- `test_submodule_content_identity_reasons_returns_reason_for_escaped_repo`
- `test_submodule_local_config_allowlist_matches_builder_outputs`
- `test_submodule_content_identity_gate_uses_no_git_content_writer_or_filter`
- `test_git_closure_reuses_precomputed_submodule_inventory`
- `test_init_submodules_from_local_source_allows_dirty_source_content`

正例:

- P-1: `test_verify_snapshot_submodule_gate_accepts_all_initialized`
- P-2: `test_verify_snapshot_submodule_content_gate_preserves_canonical_oracle_bytes`
- P-3: `test_uninitialized_nested_submodule_is_manifested_and_accepted` と既存 gitlink pin node

helper 直呼び node は単一理由を固定した。end-to-end node は統合証拠として対象理由の存在を要求し、既存 fsck 理由との併記を禁止していない。

## 実走結果

正式 runner 実走は未完了。

実装後 checkout で次の 3 node を `tools/run_tests.py` に投入した。

- `test_verify_snapshot_submodule_gate_accepts_all_initialized`
- `test_verify_snapshot_submodule_content_gate_preserves_canonical_oracle_bytes`
- `test_verify_snapshot_submodule_content_gate_rejects_worktree_blob_mismatch_with_preserved_stat`

結果は test 実行前の `qstat -Q preflight rc=1`、runner rc=16。receipt は `output/pegasus-dispatch/e5136d7884b31e64dc3800a66912ae66/receipt.json`。したがって緑とは申告せず、全 pytest node は「実装済み・未実走」である。

実行できた非受入検査:

- `python3 -m py_compile` — 2 file 成功。
- `git diff --check` — 成功。
- AST test 名検査 — 184 function、重複 0。
- 固定 `tmp_path` 相当の直接診断 — 新 helper/end-to-end/P-1/P-2/P-3/source/再帰 node が通過。
- B7 synthetic 群 14 invocation — 直接診断で通過。
- ただし直接診断は pytest runner の緑や親の受入を代替しない。

## 受理集合の変化

変更前の現行挙動:

- 空 child index/worktree、worktree bytes 改変、HEAD 外 index entry、rogue marker は、tracked `.gitmodules` の `ignore=all` と再 seal があれば受理されていた。
- `ignore=all` を外した形は既存 dirty/numstat gate が拒否。
- 再 seal を外した形は既存 fsck が拒否。
- clean initialized submodule は受理。
- uninitialized nested submodule は closure helper では manifest 化されるが、完全な `verify_snapshot` では従来どおり拒否。
- clean filter 等で Git 上 clean な CRLF worktree は受理され得た。

変更後は reject-only で、新規受理はない。追加で拒否するのは以下。

- index と `HEAD^{tree}` が異なる repository。
- index blob と raw worktree bytes、symlink target、owner execute category が異なる repository。
- CRLF 等、blob と 1 byte でも異なる worktree。
- ignored extra file、tracked path の中間 symlink。
- rogue marker、symlink admin、admin と異なる common-dir。
- replacement ref 依存の tree。
- SHA-1 以外の object format。
- seal 後 allowlist 外 local config。
- closure 無効経路と initialized descendant にある同じ不整合。

clean snapshot の oracle key 集合、canonical bytes、`submodule_manifest_sha256`、`manifest_sha256` は P-2 診断で不変だった。

## 波及と残件

所有外の直接 caller は `_submodule_inventory`、`_preflight_snapshot_relocation`、`_seal_git_object_closure`、`_build_snapshot_base`、`_derive_snapshot_from_base`、supervisor の pre/post verify、`_replay_manifest`。`collect_run`、`make_packets`、verdict CLI の独立再検証は T-1263 のままである。

B7 synthetic 群は直接診断で従来挙動を維持した。absolute gitdir/core.worktree の各 2 parameter、copy/relocation、closure 有無、empty manifest、未初期化 nested、gitlink pin を含む。

B7 real fixture 17 node は正式未実走。静的には次の影響がある。

- snapshot/closure 系 12 nodeは、新 raw/config/admin gate を追加で通る。
- supervisor/replay 系 5 nodeは、pre/post/final replay ごとに同 gate の費用が加わる。
- M6 の実測では historical pin `d706650c...` は raw 不一致 0/404、mode 不一致 0、SHA-1 であるため、正常 fixture は受理継続の見込み。
- 現 source CCBench の admin/common-dir と source config allowlist は診断で受理された。

未実走の real node は B7 記載の次の 17 件すべて: `test_parent_numstat_controls_remain_pinned`、`test_forbidden_commits_are_unreachable_in_both_cases`、`test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure`、`test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested`、`test_m1_snapshot_head_pin_is_independent`、M3 4 node、`test_snapshot_submodule_object_store_is_recursive`、`test_pos_neg_submodule_initialization_state_mismatch_is_rejected`、`test_git_answer_object_reinjection_is_rejected`、supervisor 2 node、replay node、attempt 2 node。

dev-wave worker 契約に従い、変異走行、受入、docs 記録、commit は親へ残した。

## 総括

指定 2 file に raw bytes ベースの submodule 内容同一性 gate と変異テストを実装した。  
oracle schema と正常 canonical bytes は変更していない。  
config allowlist は実 builder の段階別実測に基づき、source と seal 後を分離した。  
固定サイズ直接診断と静的検査は通過したが、正式 pytest は dispatch rc=16 のため未実走である。  
親は queue 復旧後に新 node、B7 synthetic/real、変異 matrix、受入全走を実行する必要がある。