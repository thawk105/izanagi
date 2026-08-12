## 総括

所有範囲の G-1〜G-4 を修正しました。ただし焦点 pytest は Pegasus dispatch preflight の `rc=16` で起動できなかったため、dev-wave 契約に従いすべて `partial（実装済み・未実走）` とします。docs 編集・commit・所有外ファイルの編集は行っていません。

| 所見 | 状態 | 根拠 |
|---|---|---|
| G-1 ownership transfer | partial | auxiliary close 完了後に leaf を返す [buildcache.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:314)、[buildcache.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:350)。v2 finalizer は `[binary_fd, bdir_fd]` を共通 helper に渡し、parent close 失敗時は返却予定 fd も回収 [buildcache.py:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1003)。fd-count fault injection は [test_buildcache_v2.py:1395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1395)、[test_buildcache_v2.py:1423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1423) |
| G-2 M7 単一理由性 | partial | test 側の独立 literal 6 件 [test_buildcache_v2.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:46) と production tuple の exact 一致検査 [test_buildcache_v2.py:1272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1272) |
| G-3 M8 legacy | partial | legacy は実 `_relative_entry_lexists()` が成功した直後に intermediate を swapし、`no-follow open` 拒否と swap 実在を assert [test_buildcache_v2.py:1100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1100) |
| G-4 mkdir cleanup | partial | 元例外に close/rmdir cleanup 失敗を付加した `BuildCacheError` [buildcache.py:1120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1120)。rmdir fault test [test_buildcache_v2.py:1478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1478) |
| G-5 主張限定 | partial | `buildcache.py` 側に repository-wide AST/leaf-name matching はなく、同型の限定対象は該当なし。関連 capability 検査は runtime の exact callable membership [buildcache.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:132)。pytest 未実走のため closed 申告なし |

受理・拒否挙動の対比:

- 指摘された2経路の close-error は、変更前も変更後も処理失敗として拒否されます。変更後は返却されなかった leaf fd も cleanup 対象になります。
- M7 は production 挙動不変です。tuple member 削除時に test case 自体が消えず、literal contract との不一致になります。
- M8 の symlink hit 拒否挙動は不変です。legacy の証拠だけを、lexists の先取り後に traversal が拒否する形へ再照準しました。
- `_mkdir_open_at()` の元処理失敗は引き続き拒否します。cleanup も失敗した場合、変更前は残骸理由が沈黙しましたが、変更後は元失敗と cleanup 失敗を同じ例外で報告します。

M7/M8 の単一理由性は静的には成立しています。M7 は production tuple 非依存の6ケース、M8 legacy は precheck 成功・swap 実在・`no-follow open` を固定しました。ただし変異本走は未実施です。

検査結果:

- `py_compile`（所有2ファイル）: 緑
- `git diff --check`（所有2ファイル）: 緑
- `python3 tools/check_codex_agents.py`: 緑
- `python3 tools/check_docs.py`: 緑
- 焦点 pytest: **未実走**。`qstat -Q preflight rc=1`、runner `rc=16`
- 実走済みの緑 nodeid: なし

313 passed を壊していないと考える静的根拠は、公開 signature と通常 close 成功時の返却値を維持し、production 差分を close-error cleanup と cleanup 診断に限定したこと、既存テストの期待値を反転・緩和・削除せず、M8 の拒否理由をむしろ強く固定したことです。ただし 313 件の再実測は親作業が必要です。