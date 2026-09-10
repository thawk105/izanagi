## 所見対応表

pytest 未実走のため、全件を `partial（実装済み・未実走）` とします。

| 所見 | 状態 | 根拠と関連 nodeid |
|---|---|---|
| FIX2-1 | `partial` | Git 環境 scrub と `--no-replace-objects` を追加。[s8b_floor_campaign.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:619)。`test_reseal_git_environment_scrubs_replace_and_config_authority`、`test_reseal_protocol_ignores_repository_replacement_ref`、`test_reseal_protocol_scrubs_git_config_count_injection` |
| FIX2-2 | `partial` | 書込み直前の祖先再検査と直後の realpath 検査を追加。[s8b_floor_campaign.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:753)、[s8b_floor_campaign.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:967)。`test_reseal_protocol_rechecks_ancestor_symlink_immediately_before_write`、`test_reseal_protocol_rejects_destination_realpath_outside_repo_after_write` |
| FIX2-3 | `partial` | 発行後失敗を共通診断へ集約し、exact path、再発行不能、commit 禁止を明記。[s8b_floor_campaign.py:895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:895)。`test_reseal_protocol_rejects_head_move_immediately_after_publish` |
| FIX2-4 | `partial` | 2 度目の gitlink 読取を削除し、固定 `target_pair` を post-index に使用。[s8b_floor_campaign.py:992](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:992)。`test_reseal_protocol_public_entry_accepts_unoccupied_contract_and_derived_path`、`test_reseal_protocol_rejects_head_move_immediately_after_publish` |
| FIX2-5 | `partial` | working-tree legacy との比較を廃止し、独立取得した HEAD blob の pair と sanctioned namespace を検査。[test_s8b_protocol_builder.py:1320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:1320)。`test_build_and_write_leave_repo_tree_unchanged[top-level]`、`[nested]` |

## 実装

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py)
  - 指定された Git authority 変数と全 `GIT_CONFIG_KEY_n`／`VALUE_n` をローカルに除去。
  - `GIT_NO_REPLACE_OBJECTS=1` と `git --no-replace-objects` を併用。
  - symlink 祖先を発行直前に再検査し、発行直後に destination realpath を確認。
  - 発行後の全主要失敗経路へ復旧診断を付与。
  - 恒真な gitlink 再読を削除。

- [test_s8b_protocol_builder.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py)
  - replacement ref、config-count 注入、symlink 差し替え、外部 realpath の負例を追加。
  - FIX2-4、FIX2-5 の裁定済み期待値を更新。

`s8b_floor_contract.py`、docs、`output/` は変更していません。commit も作成していません。

## 実走結果

- `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_s8b_protocol_builder.py -q`
  - `rc=16`
  - `qstat -Q preflight rc=1`
  - pytest 本体は未起動。passed/failed 件数なし。
- AST parse: `rc=0`
- `git diff --check`: `rc=0`
- `python3 tools/check_docs.py`: `rc=0`
- `python3 tools/check_codex_agents.py`: `rc=0`
- NFC・結合文字検査: `rc=0`

## 受理集合の差分

狭まったもの:

- replacement object、ambient Git config、namespace、graft、shallow authority に影響された Git 読取。
- 発行直前に sanctioned namespace の祖先が symlink 化された状態。
- 発行後の destination realpath が repository 外に出た状態。

変わらないもの:

- `freeze_protocol()`／`_freeze_protocol_parser()` の通常受理集合。
- clean repository における正規 AI reseal。
- contract 一意性、継承 16 field、canonical path／bytes の検査。
- 2 度目の gitlink 読取削除による正常時の成果物値。

## 未閉鎖

- sandbox から dispatch できず、追加・既存 pytest は未実走。
- 完全な `O_NOFOLLOW`／dirfd 配管は指定どおり実装範囲外。
- 共有 `source_digest._sanitized_git_env()` は変更しておらず、追加衛生化は floor module 内だけ。

## 総括

FIX2-1〜FIX2-5 のコードと回帰テストを実装した。  
変更は許可された campaign module と protocol-builder test の 2 ファイルだけである。  
Git authority は replacement refs と config 注入の双方から隔離した。  
書込み境界は直前の symlink 再検査と直後の realpath 検査で強化した。  
失敗 artifact の exact path と手動復旧条件を例外へ載せた。  
恒真な gitlink 再読を除去し、HEAD 移動検査を実効 gate として固定した。  
静的検査はすべて `rc=0`。  
pytest は dispatch 失敗のため、全所見とも実装済み・未実走である。