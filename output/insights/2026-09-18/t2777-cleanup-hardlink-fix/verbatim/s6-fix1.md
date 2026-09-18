## 総括

**(a) A1: closed。** 修正を実装し、指定2 file に未コミット差分を残しました。`git diff --check` は成功しました。

**(b) 変更箇所**

- [tools/dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2777-unit1-cleanup/tools/dev_wave_cleanup.py:755)：755–766行。定数と `_is_shared_object_path` に `refs`／`logs` 除外節・安全側の制約コメントを追加。
- [test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2777-unit1-cleanup/orchestrator/tests/test_dev_wave_cleanup.py:1136)：1136–1165行。`test_admin_nonobject_hardlink_is_rejected` の parameter・fixture に2件追加。既存4件の id・期待値・assertion は不変。

**(c) 全11 node の直接呼出し結果**

test module を import し、`tempfile.mkdtemp()` と `pytest.MonkeyPatch()` で実行しました。反実仮想 M5 は、メモリ上で除外節を `if False:` に変更しました。

| node | 修正後 | M5 |
|---|---|---|
| `test_admin_nonobject_hardlink_is_rejected[ref-shaped-object]` | DIRECT_CALL_PASS | 赤化※ |
| `test_admin_nonobject_hardlink_is_rejected[reflog-shaped-object]` | DIRECT_CALL_PASS | 赤化※ |
| `test_admin_nonobject_hardlink_is_rejected[gitdir]` | DIRECT_CALL_PASS | DIRECT_CALL_PASS |
| `test_admin_nonobject_hardlink_is_rejected[submodule-config]` | DIRECT_CALL_PASS | DIRECT_CALL_PASS |
| `test_admin_nonobject_hardlink_is_rejected[ref-named-objects]` | DIRECT_CALL_PASS | DIRECT_CALL_PASS |
| `test_admin_nonobject_hardlink_is_rejected[submodule-named-objects]` | DIRECT_CALL_PASS | DIRECT_CALL_PASS |
| `test_admin_shared_objects_are_removed` | DIRECT_CALL_PASS | DIRECT_CALL_PASS |
| `test_admin_read_link_race[object]` | DIRECT_CALL_PASS | DIRECT_CALL_PASS |
| `test_admin_read_link_race[registry]` | DIRECT_CALL_PASS | DIRECT_CALL_PASS |
| `test_cleanup_partial_admin_removal_reenters[None-gitdir]` | DIRECT_CALL_PASS | DIRECT_CALL_PASS |
| `test_unpublished_admin_journal_reenters[linked]` | DIRECT_CALL_PASS | DIRECT_CALL_PASS |

※ 新規2件だけが `(rc, out) == (20, "")` で AssertionError。実値は `(0, "removed\n")`、admin 撤去済みを確認しました。`DID NOT RAISE` ではありません。元の関数へ復元済みで、ソース bytes 不変も確認しました。

**(d) 変異 anchor 出現回数**

| anchor | 行 | 出現回数 |
|---|---:|---:|
| M0 最終 return 式 | 765–766 | 1 |
| M1 同上 | 765–766 | 1 |
| M2 同上 | 765–766 | 1 |
| M3 撤去側読取2行 | 994–995 | 1 |
| M4 `stable` 分岐2行 | 779–780 | 1 |
| M5 除外節2行 | 763–764 | 1 |

**(e) 受理集合は縮小方向のみ。** 中間 component に `refs`／`logs` を持つパスを共有 object の許容対象から除外しました。submodule path 自体に同 component がある真の共有 store も rc=20 となる安全側の制約です。他の読取条件・prefix 伝播・race・recovery の実装は変更していません。

**(f) 実装済み・直接呼出し実施済み。** pytest 全走、M0〜M4 の変異実走、親の mutation harness、live wave 撤去は **未実走**です。

**(g) 想定外：なし。** 報告ファイルの作成、作業リポジトリの stage・commit は行っていません。