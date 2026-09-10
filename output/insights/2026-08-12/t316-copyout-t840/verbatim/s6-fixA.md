## 総括

所有範囲内で F-1〜F-6 を実装しました。ただし Pegasus の dispatch preflight が `rc=16` で停止し、pytest は起動できていません。指示に従い、全所見を `partial（実装済み・未実走）` とします。docs 編集・commit・所有外ファイルの編集は行っていません。

| 所見 | 状態 | 根拠 |
|---|---|---|
| F-1 fd cleanup | partial | 共通 best-effort helper [buildcache.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:62)、child 登録後の親 close [buildcache.py:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:220)、`_CopiedBinary` [buildcache.py:413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:413)。fd 数実測テストは [test_buildcache_v2.py:1288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1288)、[test_buildcache_v2.py:1308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1308)、[test_buildcache_v2.py:1340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1340) |
| F-2 capability identity | partial | original callable snapshot と platform capability 判定 [buildcache.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:55)、[buildcache.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:132)。delegate wrapper 正例 [test_buildcache_v2.py:1276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1276) |
| F-3 staging binding | partial | staging fd を保持し、parent/name identity 再照合後に直接 copy [buildcache.py:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:449)、v2 [buildcache.py:1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1381)、legacy [buildcache.py:1596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1596)。swap 負例 [test_buildcache_v2.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1404) |
| F-4 environment negatives | partial | `/proc/self/fd` reopen probe [buildcache.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:77)。set 欠如、dir-fd 6 membership、follow-symlinks、procfs の負例 [test_buildcache_v2.py:1234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1234) |
| F-5 mutations | partial | M5 [test_buildcache_v2.py:1013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1013)、M7 [test_buildcache_v2.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1243)、M13 [test_buildcache_v2.py:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:968)。M2/M8 の限定も docstring に反映 |
| F-6 cleanup/claims | partial | `_mkdir_open_at()` の途中失敗時に作成 entry を回収 [buildcache.py:1092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1092)、負例 [test_buildcache_v2.py:1359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1359)。gate-order/helper-only の証拠範囲も明記 [test_buildcache_v2.py:1156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1156) |

受理・拒否挙動の差:

- delegate wrapper は以前 platform 欠如と誤判定されましたが、変更後は受理します。実 capability membership 欠如、定数欠如、procfs 不可は引き続き拒否します。
- staging entry swap は以前、別 pathname の binary をコピーできました。変更後は held fd と parent/name の不一致で拒否します。
- close 失敗時も後続 fd の close を試み、最初の close 例外を返します。
- `_mkdir_open_at()` の途中失敗は、失敗自体を受理せず、作成済み entry も回収します。
- 正常経路、既存 cache-hit compatibility、directory publish の原子性契約は変更していません。

変異の単一理由性は静的には次の形へ揃えましたが、未実走です。

- M5: `verify_destination_entry()` 全無効化だけで hash 後 swap が生存。
- M7: 個別 capability membership 検査の除去だけで負例が生存。
- M13: `CMakeCache.txt` 1 member の clean candidate 混入だけで exact-set test が赤。
- M2: FIFO のみを evidence とし、directory は除外。
- M8: binary intermediate symlink のみを evidence とし、metadata は除外。

`test_v2_two_real_processes_only_one_claims` は HEAD と直接比較し、本文を一文字も変更していません。

検査結果:

- `py_compile`（所有3ファイル）: 緑
- `git diff --check`: 緑
- `python3 tools/check_codex_agents.py`: 緑
- `python3 tools/check_docs.py`: 緑
- platform probe: required membership 全件および `/proc/self/fd` reopen 成功
- 焦点走、collect-only、`test_buildcache_v2.py` 全体: すべて pytest 起動前に `qstat -Q preflight rc=1`、runner `rc=16`。したがって緑の実走 nodeid はありません。

所有外への波及候補は `pipeline.py`、`s8b_floor_campaign.py`、各 calibration/qualification/oracle driver と、`test_campaign.py`、`test_build_site_gate.py`、`test_s8b_materialization.py`、floor/oracle/qualification 系 consumer test です。公開 `build()` / `build_v2()` の signature は不変で、変更した `_secure_copy_binary()` は静的検索上、所有ファイル内の2 production call-siteと1 test call-siteだけです。