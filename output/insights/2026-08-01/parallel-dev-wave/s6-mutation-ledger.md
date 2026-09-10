# 段 6 変異台帳 — parallel-dev wave ([T-220] / D109)

- 本走 anchor commit: `4837ffc` (merge commit、`DW-O19` の「本走は統合 commit 後」を満たす)
- harness (repo 外・非 commit): `/home/SFC/tanab/.claude/jobs/6e0f3aa9/tmp/mutation/harness.py`
  (spec = 同 dir `mutations.py`、結果 = `results/summary.json` と `results/V*.log`)
- 実行経路: `python3 tools/run_tests.py <対象ファイル> -q -rf` で Pegasus 計算ノードへ同期 dispatch。
  **ログインノードでは pytest を 1 度も走らせていない**
- ベースライン: 対象 4 test ファイルすべて rc=0・失敗 node ゼロ (変異前)。**全ての赤は変異に帰属する**

## 結果 — 15/15 KILLED、SURVIVED ゼロ、非登録ゼロ

| ID | 変異 | 判定 | 赤くなった test node (`DW-M08` 正規化形) |
|---|---|---|---|
| V1 | `_handoff_snapshot` に名前形拒否 (`.md` 以外を `_Reject`) を再導入 | KILLED | `test_dev_wave_land.py::test_foreign_handoff_of_any_shape_does_not_block_land` / `::test_nested_untracked_under_foreign_handoff_directory` |
| V2 | 同所に `stat.S_ISREG` 要求を再導入 | KILLED | 同上 2 本 |
| V3 | `README.md` skip を削除 | KILLED | `::test_handoff_readme_remains_a_landable_target` / `::test_untracked_handoff_readme_colliding_with_target_is_rejected` |
| V4 | `_verify_main_clean` の handoff 分岐を無条件 `continue` | KILLED | `::test_untracked_handoff_readme_colliding_with_target_is_rejected` (登録判別入力) + `::test_colliding_untracked_rejected_without_main_or_foreign_artifact_change` + `::test_untracked_nested_repository_record_collides_with_target` |
| V5 | 同分岐の前方一致を集合メンバシップに | KILLED | `::test_nested_untracked_under_foreign_handoff_directory` のみ |
| V6 | `identities` に per-entry 内容 `sha256` を戻す | KILLED | `::test_foreign_handoff_edited_in_place_around_status_does_not_block_land` のみ |
| V7 | `_ControlSnapshot` の比較対象から `handoffs` を落とす | KILLED | `::test_foreign_handoff_appearing_mid_flight_is_still_rejected` / `::test_foreign_handoff_disappearing_mid_flight_is_still_rejected` |
| V8 | `docs/handoff` の dir identity を落とす | KILLED | `::test_handoff_directory_replacement_around_status_is_still_rejected` のみ |
| V9 | `_postcondition` 成功枝を `_verify_main_clean` へ戻す | KILLED | `::test_post_land_is_not_failed_by_foreign_handoff_activity` のみ |
| V10 | status レコードの `rstrip(b"/")` 正規化を外す | KILLED | `::test_untracked_nested_repository_record_collides_with_target` のみ |
| V11 | `check_docs` の handoff warning を finding へ (2 箇所累積) | KILLED | `test_check_docs.py::test_stale_active_handoff_does_not_make_check_docs_red` / `::test_unknown_state_value_is_a_warning_not_a_finding` / `::test_malformed_four_line_header_is_a_warning_not_a_finding` / `::test_short_base_commit_is_a_warning_not_a_finding` |
| V12 | `pytest.ini` に `addopts = -q` | KILLED | `test_pytest_collection_config.py::test_repo_pytest_ini_has_no_addopts_and_pins_testpaths` のみ |
| V13 | `pytest.ini` から `testpaths` を削る | KILLED | `::test_bare_pytest_collection_is_scoped_by_testpaths` (挙動的正例・毒を実収集) / `::test_repo_pytest_ini_has_no_addopts_and_pins_testpaths` / `::test_ini_testpaths_and_runner_default_target_point_at_the_same_tree` |
| V14 | `check_ai_provenance` の実装面分類から `pytest.ini` を外す | KILLED | `test_check_ai_provenance.py::test_repo_root_pytest_ini_requires_codex_author` / `::test_repo_ships_the_pytest_ini_that_the_classifier_now_covers` / `::test_implementation_path_contract[pytest.ini-True]` / `::test_implementation_path_contract[./pytest.ini-True]` |
| V15 | `_verify_main_no_tracked_dirt` の本体を `return None` に | KILLED | `::test_tracked_dirt_appearing_after_successful_merge_is_postcondition_failed` のみ |

## `DW-M01` の確認

全 15 件について「その位置より前に同じ入力を拒否する検査がないこと」「無効化時の赤理由が
一つに絞れること」をコードで確認した。**非登録に回した変異はゼロ**。

## `DW-M03` の kill 意味論 — 数えなかったもの

- **V13 の 4 本目 `test_norecursedirs_excludes_generated_hidden_and_vendor_trees` は
  独立した検出力として数えない。** 赤の理由は helper `_ini_without` が出荷 ini から
  `parser["pytest"]["testpaths"]` を読むための `KeyError: 'testpaths'` であり、**fixture 由来の
  アーティファクト**である。V13 の実効 kill は挙動的正例
  `test_bare_pytest_collection_is_scoped_by_testpaths` (`assert 2 == 0` = 毒 `poison_test.py` を実収集) と
  config pin 2 本が担う

## 段 3 の懸念に対する実測の答え

段 3 の敵対レンズは V4 / V5 / V8 / V13 が「殺せない」と指摘した。裁定 B3 で再照準した結果:

- **V4**: 無条件 `continue` は衝突検査そのものを殺す粗い変異なので 3 本が赤になる。
  裁定どおり untracked README の fixture (rc=20 DIRT vs 24 NOT_LANDED) を判別入力として登録した
- **V5**: 「素の `in`」を集合メンバシップと読んだ。nested 衝突が `RC_CONTROL_PLANE`(21) から
  `RC_DIRT`(20) へ落ちる差だけで赤になる。**rc を判別しない test なら緑になっていた**
- **V8 は等価変異ではなかった。** 裁定 B3 が条件付きにした「子エントリを保存したまま dir を
  差し替える」`_WRAPPER` mode (`swap-handoff-dir`) が実在し、名前集合一致・inode 相違を作れるため、
  **dir identity 単独の検出力が実証された**
- **V13**: 毒の置き場を `output/` 配下から **repo 直下**へ移して判別可能にした
  (`output/` 配下だと `norecursedirs` の `output` にも当たり `testpaths` 欠落を検出できない)

## harness の契約充足 (`DW-M04` / `DW-M05` / `DW-M06`)

- **一意性**: 全 16 置換について「対象ファイル内 1 箇所 / repo の他 tracked file 0 箇所 = repo 全体で 1」を
  `--check-anchors` と本走の両方で assert。非一意により登録を見送った変異はない
- **単一走行 guard**: `harness.lock` に `flock(LOCK_EX|LOCK_NB)`、取得失敗で abort
- **復元**: 各変異の `finally` で元ソースを書き戻し `read_text() == 元ソース` を assert (15/15)。
  最終にも全 4 ファイルを再検査。**未追跡・未 stage に恒真な `git diff` は使っていない**
- **実行時間上限からの独立**: `setsid` + `nohup` で親の上限に掛からない経路から起動 (F32 対策)。
  timeout 発火なし (`DW-M06` は不発火)
- **git 状態変更なし**: commit / add / reset / checkout / stash / branch は不使用。
  最終 `git status --short` は**空**、HEAD は `4837ffc` のまま (親が独立に再確認した)
