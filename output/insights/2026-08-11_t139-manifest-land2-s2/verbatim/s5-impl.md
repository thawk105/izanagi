実装範囲 8/8 をコード・テストへ反映しました。commit、`docs/`、`output/` の編集はしていません。

### 実装内容

- [blobref.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s2/orchestrator/preregistration/blobref.py:21)
  - `PATH` を継承 allowlist から除外。
  - `/usr/bin/git` を module-private な固定絶対 path として起動。
  - `--no-pager`、`core.commitGraph=false`、`core.fsmonitor=false` を全 Git 呼出しへ付与。
  - 親由来の全 `GIT_*` を破棄し、安全値のみ再設定。`GIT_CONFIG_NOSYSTEM=1` と `GIT_NO_LAZY_FETCH=1` を強制。
  - `objects/info/{alternates,http-alternates}`、`*.promisor`、`extensions.partialClone`、有効な `remote.*.promisor` を事前拒否。
  - 固定 Git path が存在しない場合は「git executable を解決できない」と識別可能な `BlobResolutionError`。
  - owner／digest 検査は実装していない。

- [test_t139_blobref_git_trust.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s2/orchestrator/tests/test_t139_blobref_git_trust.py:40)
  - 正例を含む新規 10 test。
  - PATH 上の偽 Git は marker で未実行を検査。
  - `GIT_DIR`、global config、alternate object directory 等の注入を検査。
  - 外部 alternate object store、promisor config／marker、partial clone を個別に拒否。
  - 壊れた commit-graph と fsmonitor hook は挙動で検査。
  - 全 subprocess の絶対 argv、pager／commitGraph／fsmonitor 引数、NOSYSTEM を assert。

### 設計判断

絶対 path は `/usr/bin/git` 固定を選びました。`shutil.which`／親 `PATH`、複数候補探索、caller 注入はいずれも trust root を実行環境や入力へ広げるため不採用です。

alternates／promisor は `-c` だけでは repository 内の object-store 状態を無効化できないため、既存の grafts 検査と同様に状態の存在を fail-closed で拒否しました。`GIT_NO_LAZY_FETCH` は競合時の補助防壁です。

pager は stdout が常に非 TTY の一時 file で、NOSYSTEM は安全に `/etc/gitconfig` を変更できないため、挙動による単一理由テストを作れません。この2項目は全実 Git argv／env の assert で固定しています。

### 受理・拒否挙動

変更前は正常 repo、固定 commit・regular blob・一致 digest を受理し、shallow／replace refs／grafts 等を拒否していました。一方、親 `PATH` による名前解決と repository alternates／promisor は受理され得ました。

変更後も正常 repoと `remote.*.promisor=false` は受理します。新たに固定 Git 不在、alternates marker、promisor pack/config、partial-clone config を拒否します。その他の BlobRef shape、digest、size、history gate は変更していません。

所有外の波及先は `approval_payload.load_approval_payload`、`erratum.compose_core`、package の既存 `read_pinned_blob` export、および指定された既存 T-139 test 3 fileです。共有 fixture の変更はなく、新 fixture は新 test file 内だけです。

### 検査結果

- `check_codex_agents.py`: rc=0
- `check_docs.py`: rc=0
- `git diff --check`、変更2 fileの AST parse: 成功
- pytest は未実走。次の範囲を `tools/run_tests.py` で再試行しましたが、すべて collection 前に `qstat -Q preflight rc=1`、runner `rc=16` でした。
  - 新規 trust-root test
  - 指定された既存 T-139 test 3 file
  - `test_plain_runner_coverage.py`
- assertion 赤は未観測ですが、緑とも申告しません。実装済み・未実走です。

開始後に所有不明の未追跡 `output/insights/2026-08-11_t139-manifest-land2-s2/` が現れました。削除・編集していません。

## 総括

- 実装対象: 8/8（新規 test 10件）。
- pytest: infrastructure `rc=16` のため未実走・未収集。
- 静的 checker: すべて rc=0。
- 未解決: 親環境で対象5 test fileの実走と段6変異検査が必要。