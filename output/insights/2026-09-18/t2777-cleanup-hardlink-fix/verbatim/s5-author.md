## 総括

実装済みです。指定2ファイルだけに未コミット差分を残しました。`git diff --check` は成功しています。

**(a) 変更箇所**

- [tools/dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2777-unit1-cleanup/tools/dev_wave_cleanup.py:752)：752–783行に regex・`_is_shared_object_path`・読取条件、793–821行の `_admin_snapshot`、972–993行の `_remove_admin_entries`、1045行の呼出し。
- [test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2777-unit1-cleanup/orchestrator/tests/test_dev_wave_cleanup.py:1095)：1095–1214行に helper・新規7 node、1219–1280行と1369–1430行の recovery テストへ追加 assertion。

**(b) 直接呼出しと反実仮想**

全 node は `test_dev_wave_cleanup.py::` 配下です。

| node | 本実装 | 一時変異での結果 |
|---|---|---|
| `test_admin_shared_objects_are_removed` | DIRECT_CALL_PASS | M2・M3で赤化 |
| `test_admin_nonobject_hardlink_is_rejected[gitdir]` | DIRECT_CALL_PASS | `return True` で DID NOT RAISE |
| `test_admin_nonobject_hardlink_is_rejected[submodule-config]` | DIRECT_CALL_PASS | M1で赤化 |
| `test_admin_nonobject_hardlink_is_rejected[ref-named-objects]` | DIRECT_CALL_PASS | M1で赤化 |
| `test_admin_nonobject_hardlink_is_rejected[submodule-named-objects]` | DIRECT_CALL_PASS | M1で赤化 |
| `test_admin_read_link_race[object]` | DIRECT_CALL_PASS | object 用 stable 分岐を無効化すると ValueError |
| `test_admin_read_link_race[registry]` | DIRECT_CALL_PASS | M4で DID NOT RAISE |
| `test_unpublished_admin_journal_reenters[linked]` | DIRECT_CALL_PASS | M2・M3で赤化 |
| `test_cleanup_partial_admin_removal_reenters[None-gitdir]` | DIRECT_CALL_PASS | M2・M3で赤化 |

M2は preflight の rc=20、M3は rc=30・`phase=admin-remove` を確認しました。M0では全9 nodeが通りました。変異はメモリ上で適用・復元し、ソースが不変であることも確認済みです。

**(c) anchor 出現回数**

M0・M1・M2の return 行、M3の指定2行、M4の指定2行は、いずれも **1回**です。

**(d) 静的な波及確認**

- `_read_admin_file` の既定呼出し6件は不変：631行の resolver、847・848行の gitdir／commondir、896・1031・1052行の journal。
- 共有 fixture、既存 journal hardlink 負例、recovery の parameter・既存 assertion は不変。
- `test_pytest_collection_config.py` が参照する `test_real_occupancy_scan_rejects_live_process_cwd` と `test_git_argv_spy_sees_only_allowlisted_cleanup_commands` は不変。
- README・mutation harness・consumer test は編集していません。

**(e) 受理集合の差**

従来の一律 nlink==1 から、指定された object 名前形の regular file に限り nlink>1 を許容します。registry・journal・symlink・特殊 file・操作 marker・入口の nlink==0 拒否は維持しています。撤去対象は自 wave の admin のままです。

object 読取では nlink／ctime の変化を許容するため、ctime だけに残る変更履歴の検出は弱まります。dev／ino／mode／size／mtime と撤去直前の length・sha256 照合は維持しています。

**(f) 未実走**

pytest 全走、親の mutation harness、実 wave 撤去は **未実走**です。今回の直接呼出しは親の全走を代替しません。

**(g) 想定外・引継ぎ事項**

- 負例では `git status` が index の inode を更新したため、そのテスト内だけ `GIT_OPTIONAL_LOCKS=0` を設定しました。木の inode・bytes 不変 assertion は維持しています。
- 裁定の M1 `return parts[0] == "modules"` は gitdir 負例を赤化しません。実測でも同 node は通り、modules 側3件だけが赤化しました。gitdir の赤化は別途 `return True` で確認済みです。親の期待 node 集合に反映が必要です。