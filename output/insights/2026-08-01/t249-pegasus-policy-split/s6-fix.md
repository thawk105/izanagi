実装を完了しました。F1〜F5・F7 は closed、F6 は裁定どおり保証範囲を限定した partial です。C-2、D-7、floor shell、policy 値、protected path は変更していません。

### 所見対応

| 所見 | 状態 | 変更前 → 変更後 |
|---|---|---|
| F1 | closed | walltime の文字列／秒 drift が未検出 → smoke/certify/floor の相互一致を検査。reserve は certify の既存 `finalize_reserve(600)` 式へ束縛 |
| F2 | closed | Git pathspec の wildcard 偽陽性あり → `git ls-files -z` を一度取得・cache し、decoded exact set membership で判定 |
| F3 | closed | nested directory を無視 → registry 以外の directory・symlink・special entry を明示拒否 |
| F4 | closed | registry／ancestor symlink を追従 → registry・policy directory・全 component を `lstat`、symlink 拒否、strict resolve containment を確認してから registry を読む |
| F5 | closed | calibration policy symlink を `-f` が受理 → certify 系2 shellのみ `-L` で exit 2。共有 policy 検査は無変更 |
| F6 | partial | 網羅的に見える表現 → test 名・docstring で direct literal read の best-effort tripwire と限定。検出可能な positive control を固定 |
| F7 | closed | nested `with` の同名 handle を shared read と誤認 → AST binding を追跡して shadowing を除外。直接 shared read は引き続き拒否 |

F1 の配置は以下です。

- smoke/certify・reserve: [test_pegasus_tools.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:126)
- floor: [test_pegasus_floor_tools.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_floor_tools.py:317)
- F2〜F4/F6/F7: [test_pegasus_policy_registry.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:45)
- F5: [certify_calibration.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/certify_calibration.sh:110)、[submit_certify.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/submit_certify.sh:56)

`certify_walltime_s=7199` の in-memory 変異では、新しい相互一致 assert が `RED` になることを静的確認しました。実ファイル変異を伴う pytest 本走は親の anchor commit 後の契約なので未実施です。

### 検査結果

成功:

- `python3 -m py_compile`：変更した3 test file
- `bash -n`：certify 系2 shell
- `git diff --check 7b24f81`
- direct-read positive control：`[(3, "certify_walltime_s")]`
- nested shadowing control：finding 0
- 現行 live consumer scan：finding 0
- literal `*.json` exact tracked 判定：false
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

pytest dispatch は両方とも収集前に `qstat -Q preflight rc=1`、rc=16 で停止しました。

- 3 file 全体：`test_pegasus_tools.py`、`test_pegasus_floor_tools.py`、`test_pegasus_policy_registry.py`
- F42：`test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`

したがってpytest の緑は主張しません。F42 は新 test file の既存 self-runnerが維持されていることだけ静的確認済みです。

### 受理集合と波及

production の正常入力・値は不変です。承認された縮小は calibration symlink の拒否、pytest gate の nested/special/pathspec/symlink/drift 拒否です。F7では正当な nested task-policy read の過剰拒否だけを除去しました。

所有外への静的波及候補:

- caller：`submit_certify.sh → certify_calibration.sh`、`submit_floor.sh → floor_campaign.sh`
- fixture：calibration の `copytree(TOOL_DIR)`、floor の明示 policy copy
- consumer test：Pegasus tools／floor tools
- submit path を参照する `test_hooks.py`／`guard_bash.py`
- registry tracked 判定が依存する Git index

### Git 状態

`git status --short`:

```text
M  orchestrator/tests/test_pegasus_floor_tools.py
AM orchestrator/tests/test_pegasus_policy_registry.py
MM orchestrator/tests/test_pegasus_tools.py
MM tools/pegasus/certify_calibration.sh
M  tools/pegasus/floor_campaign.sh
A  tools/pegasus/policies/calibration_v1.json
A  tools/pegasus/policies/floor_v1.json
A  tools/pegasus/policies/registry_v1.json
MM tools/pegasus/submit_certify.sh
M  tools/pegasus/submit_floor.sh
```

親の staged snapshot は維持し、今回の fix は4 fileの unstaged 差分です。Git index操作・commitは行っていません。

`git diff --stat`:

```text
 orchestrator/tests/test_pegasus_policy_registry.py | 217 ++++++++++++++++-----
 orchestrator/tests/test_pegasus_tools.py           |  40 ++++
 tools/pegasus/certify_calibration.sh               |   2 +-
 tools/pegasus/submit_certify.sh                    |   2 +-
 4 files changed, 210 insertions(+), 51 deletions(-)
```

base `7b24f81` からの総差分は10 file、638 insertions / 36 deletionsです。

指定 protected-path 検査は rc=0:

```text
git diff --exit-code 7b24f81 -- tools/pegasus/policy.json output/env/pegasus orchestrator/qualification/t126_reservation_policy_v1.json
```

`tools/pegasus/policy.json` SHA-256 は引き続き `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac` です。

## 総括

- F1〜F5・F7を実装上 closed、F6を裁定どおり partial とした。
- walltime 3組の文字列／秒一致と、reserve 600秒の既存式束縛を追加した。
- tracked exact判定、flat閉集合、全component symlink・containment検査を追加した。
- certify系2 shellだけ calibration symlinkを拒否し、共有policy検査は変更していない。
- live scanはbest-effortと明記し、positive controlとF7 shadowing controlを固定した。
- 静的検査は成功、pytest/F42はdispatch rc=16で未実測。
- protected pathはrc=0、policy hash不変、docs・commit・index操作なし。
- 親は最終stage後に3 file、F42、M6実変異を計算ノードで実測する必要がある。