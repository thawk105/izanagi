## 総括

問題 1・2 ともテストだけで修正しました。production・docs は未変更、commit も作成していません。pytest は dispatch preflight の `rc=16` で起動できなかったため、判定は双方とも `partial（実装済み・未実走）` です。

| 問題 | 判定 | 根拠 |
|---|---|---|
| M5 anchor の非決定性 | partial | [test_buildcache_v2.py:1033](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1033) |
| M11 等価変異 | partial | [test_p3_build_authority_cli.py:676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:676) |

### 問題 1 — root cause

旧テストは `full_sha256()` を差し替え、その返却直後に destination entry を rename していました。しかし `full_sha256()` は `_full_sha256_fd()` の二度の `fstat` の間で呼ばれています。[buildcache.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:421)

rename は held inode の `ctime` を更新し、`_stable_file_identity()` は `ctime_ns` を比較します。[buildcache.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:182)

そのため timestamp tick により結果が分岐していました。

- `ctime_ns` が変わる: `binary が sha256 中に変化した` で早期拒否
- 同一 tick に収まる: 本来の `destination entry` 不一致へ到達

実際の変異ログにも両結果が残っており、これがフレークの root cause です。

修正後は `_full_sha256_fd()` 全体の完了後に swap します。対象 path は探索せず `/proc/self/fd/<fd>` から一意に取得し、fsync も mode `0o500` の最初の file ではなく、hash に使った exact fd だけを記録します。[test_buildcache_v2.py:1035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1035)

`full_sha256` の複数呼出しは root cause ではありません。fresh v2・legacy はそれぞれ `_full_sha256_fd()` を一度だけ呼びます。[buildcache.py:1455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1455)、[buildcache.py:1664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1664)。修正後のテストも二度目の呼出しを明示的に拒否します。

### 性質を弱めていないこと

変更前後で次の最終 assert は維持しています。

- `destination entry` 不一致による拒否
- nm・sha256・fsync が同一 inode
- `.publish-*` が残らない
- `ycsb_silo.exe` が残らない

該当箇所は [test_buildcache_v2.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1060) です。観測は pathname/mode 推定から exact held fd へ強化されています。

### 問題 2 — M11 再照準

既存 decoy は許可 path より長い suffix/nested path だけでした。そのため変異 `allowed_path.startswith(relative_path)` は常に偽で、exact match と意味が変わりませんでした。

許可 path `.../smoke_driver.py` の真の前方一致 `.../smoke_driver` を synthetic path として実 matcher に渡し、実 call が違反として返ることを追加しました。[test_p3_build_authority_cli.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:692)

変異後は許可 path が prefix decoy に誤って一致し、expected 側へ許可 entry が混入します。assert された違反集合と一致しなくなるため、次の単一 node・単一理由で赤になる見込みです。

`test_low_level_issuer_allowlist_rejects_prefix_and_nested_paths`

### 検査

- `py_compile`（変更した2ファイル）: 緑
- `git diff --check`: 緑
- `python3 tools/check_codex_agents.py`: 緑
- `python3 tools/check_docs.py`: 緑
- 焦点 pytest:
  - M5 node（legacy / v2 の2 parameter）
  - M11 matcher node
  - 結果: pytest 起動前に `qstat -Q preflight rc=1`、runner `rc=16`
  - よって実装済み・未実走

変更ファイルは指定された2テストだけです。