fixture 修正は実装済みですが、実走できなかったため 4 件とも `partial` です。緑・closed は主張しません。

### 対応表

| 赤 | 対応 | 状態 |
|---|---|---|
| buildcache 下位行 drift | stable 版を配置後に期待値を作り、下位行だけ changed へ変更 | `partial` |
| deterministic across roots | receipt 付き v2 較正と固定 toolchain 観測を注入 | `partial` |
| journal manifest precedence | 同上 | `partial` |
| happy path resolves/loads | 同上 | `partial` |

変更箇所は [test_buildcache_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_buildcache_v2.py:420) と [test_s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_s8b_ratified_freeze.py:333) のみです。

ratified fixture では production validator 由来の v2 較正を作り、acquisition receipt、compiler/CMake の固定観測、期待 toolchain manifest の exact assertion を追加しました。実 compiler・実 CMake は読みません。

焦点 4 nodeid は `tools/run_tests.py` で起動しましたが、`qstat -Q preflight rc=1` により runner が `rc=16` で停止しました。構文解析、`git diff --check`、`check_codex_agents.py`、`check_docs.py` はすべて rc=0 です。

所有外への静的波及候補は、共有 helper を利用する同ファイル内の他 emitter/g2 テスト、`test_schema_v2.py` の v2 fixture、production の `_run_campaign_core`／`build_cells`／`build_v2` 引数契約です。

## 総括

- 赤 4 件: すべて `partial`（fixture 修正済み・未実走）、`closed=0`、`regressed=0`
- production: 開始時からの既存 dirty 差分には触れず、編集操作は所有テスト 2 ファイルだけ
- 実走: 指定 4 nodeidを一括起動したが `rc=16`（`qstat -Q rc=1`）で未実走
- 強度: 専用エラーメッセージ、exact-key、既存 SHA assertion は不変で、fake build assertion を追加
- 波及: 同ファイルの共有 emitter helper、v2 schema fixture、floor/buildcache の引数契約に可能性あり