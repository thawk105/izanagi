## 総括

段 5 実装子 A の所有範囲 3 ファイルだけを変更しました。commit・docs 編集・fixture hash 差替え・xfail 化は行っていません。

- [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:76)
- [coder_effect_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/coder_effect_gate.py:1)
- [test_buildcache_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:916)

実装内容:

- POSIX constants・`dir_fd` capability の fail-closed 検査。
- staging/source/clean の no-follow dir-fd 走査。
- regular file・`nlink==1`・特権 mode 拒否と copy 前後の source 不変性検査。
- destination create-only、`0o500`、held fd による nm・SHA・fsync・publish inode 再照合。
- v2/legacy とも clean candidate へ binary だけを copyし、metadata は host-generated create-only。
- hit 時の manifest・sidecar・binary の held-fd/beneath-only 読み。
- stale symlink・非 directory・broken leaf symlink の拒否。
- gate failure 時の staging/clean 全破棄と、v2 claim 残置。
- directory publish の create-only 原子性が残余であることを docstring に明記。
- lexical gate と post-build copy-out の関係、T-841 残余、非 security-boundary 性を追記。

主張範囲は cache publish 時点の inode 厳格化だけです。host-security boundary、certified safety、実行時 binary identity は保証しません。

### 受理・拒否集合

変更前:

- fresh は CMake tree 全体を publish。
- unallowlisted 偽 metadata があると create-only metadata 書込みと衝突。
- symlink-to-regular と hardlink の allowlisted leaf を受理。
- FIFO/directory leaf は既に拒否。
- legacy broken leaf symlink は stale 扱いで削除・再buildし得る。
- hit の binary 中間 symlink は path-based read で追跡。
- binary mode は staging の mode を保持。

変更後:

- unallowlisted CMakeCache/object/symlink/FIFO/偽 metadata は開かず、fresh 自体は受理して最終集合から除外。
- allowlisted symlink、hardlink、特殊 file、特権 mode、不変性違反、namespace symlink は拒否。
- binary は常に `0o500`。
- hit の旧 extra member は互換性のため引き続き受理。member allowlist は遡及強制しない。
- legacy broken leaf symlink は再buildせず拒否。
- 非対応環境は silent degrade せず拒否。

### テスト

46 expanded case 相当の新規制御を追加しました。内容は legacy/v2 正例、leaf 4 種負例、same-fd TOCTOU、publish inode、hit symlink、旧 extra member、gate 順序、fd対応 nm、5 constants、失敗 matrix、clean 中間 symlink、relative path、M6/M13 専用 anchorです。

pytest は**実装済み・未実走**です。以下を含む `tools/run_tests.py` 実行を繰り返しましたが、すべて pytest 起動前に停止しました。

- `orchestrator/tests/test_buildcache_v2.py`
- 新規 environment-contract node
- 既存 fresh/manifest/concurrency node
- `--collect-only`

共通失敗:

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
NQSconnect: [API EACCTAUTH] Unknown user-id
```

直接 pytest は実行していません。したがって緑の nodeid、collection 完了、`KILLED` は申告しません。

実走済みで緑:

- `python3 tools/check_codex_agents.py` — rc=0
- `python3 tools/check_docs.py` — rc=0
- 3 ファイルの AST parse、test module import、`git diff --check` — 成功
- test 名重複・xfail/skip 追加なしを静的確認

揮発する working-tree hash 等は期待値へ入れていません。SHA は固定 payload を独立 `hashlib.sha256` で計算しています。既存 fixture hash は未変更です。

### 変異 anchor

すべて実装済みですが未実走です。

| 変異 | 単一理由 anchor |
|---|---|
| M1 | source leaf symlink。leaf pre-stat に先取りさせず `O_NOFOLLOW` open が唯一の拒否点 |
| M2 | FIFO が `S_ISREG` の anchor。directory は判定削除後も `read(EISDIR)` に先取りされる |
| M3 | hardlink の `nlink==1` |
| M4 | clean 中間 component の既設 symlink |
| M5 | nm/SHA/fsync の inode 観測と destination 差替え |
| M6 | byproduct のない専用 fixtureで forged metadata bytes のみを比較 |
| M7 | `monkeypatch.delattr` による各 constant 欠落 |
| M8 | binary 中間 symlink が単一 anchor。metadata symlink は旧 `islink` 検査にも先取りされ得る |
| M12 | 正常 `nlink=1` executable 正例 |
| M13 | 偽 metadataなし、CMakeCache/object だけを置く専用 exact-set anchor |

### 波及可能性

所有外の主な caller/consumer:

- `pipeline.py`
- `s8b_floor_campaign.py`
- `s1_verify_extime_calibration.py`
- `s2_verify_calibration.py`
- `s3_lock_coverage.py`
- `s5_permutation_coverage.py`
- `backoff_profile.py`
- `backoff_overthrottle.py`
- `between_run_floor.py`
- `pegasus_floor_scoping.py`

関連共有 fixture/test は `test_campaign.py`、`test_build_site_gate.py`、`test_s8b_floor_campaign.py`、qualification/oracle driver 系です。親の関連全走が必要です。

`durable_root.py` は使用していません。現 API は root fd を保持せず、dir-fd component traversal/mkdir APIもないため、編集なしでは再利用不能でした。再利用するなら同ファイルに held-root capability と openat/mkdirat 相当 API の追加が必要です。