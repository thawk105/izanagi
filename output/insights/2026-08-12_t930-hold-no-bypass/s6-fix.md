実装は完了しました. docs 編集と commit はありません. ただし Pegasus dispatch 障害のため指定 test は未実走です.

## 所見別対応

| 所見 | 状態 | 対応 |
|---|---|---|
| revA 1 BLOCKER | partial | active pytest session 印を追加し, manual/none runner は module import 時に拒否する実装済み. 実走未了 |
| revA 2 MAJOR | partial | campaign の fixture node と plain runner を collection/import 段階で検査する test へ変更済み. 実走未了 |
| revA 3 MINOR | partial | noncallable 負例を追加. JSON canonicalization は契約として残し, 非 ASCII を含む raw 文字列を直接 pin. 実走未了 |
| revA 4 MINOR | partial | `103 passed` literal を rc, refusal prefix, `1 skipped`, passed >= 1 の意味契約へ置換. 実走未了 |
| revB 1 BLOCKER | closed | 親の実測で fixture/parametrize 解除経路が閉じているため追加変更なし |
| revB 2 MAJOR | partial | revA 4 と同じ意味契約へ置換済み. 実走未了 |

`regressed` は 0 件です.

## 変更内容

- [growth_test_holds.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/growth_test_holds.py:216), lines 216-301
  - active pytest config identity の mark/unmark API を追加.
  - `plain_runner="pytest-delegating" | "manual" | "none"` を必須化.
  - session, exact token, `__main__` pytest delegation の順で受理し, その他を import 時拒否.
  - call-time wrapper は維持.
  - canonical JSON 生成を共通化.

- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/conftest.py:41), lines 41-84, 520-524, 904-915
  - `pytest_configure` で session mark.
  - `pytest_unconfigure` で該当 config identity のみ unmark.
  - `ModuleNotFoundError(name="orchestrator")` fallback は mark API を `None` にして fail-open を維持.
  - skip marker の付与場所は `pytest_collection_modifyitems` のまま.

- [test_growth_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_growth_test_holds_contract.py:337), lines 4-33, 337-435, 485-720
  - runner 宣言と `__main__` 内の `pytest.main` を照合する AST 検査.
  - pytest delegation を `manual` と偽る負例.
  - noncallable namespace 負例.
  - canonical ASCII JSON の raw pin.
  - campaign fixture node の `--noconftest` import-stage 検査.
  - campaign plain runner が `PASS ` と passed summary 前に止まる検査.
  - exact token で import 後に token を外す call-time wrapper 検査.
  - F2 の意味ベース summary parse.

- 8 held module の宣言:
  - [test_campaign_import_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_campaign_import_invariant.py:1707), lines 1707-1708, `manual`
  - [test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_codex_reasoning_ab.py:4269), lines 4269-4270, `pytest-delegating`
  - [test_env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_env_attestation.py:1359), lines 1359-1360, `pytest-delegating`
  - [test_ruleops.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_ruleops.py:3455), lines 3455-3456, `none`
  - [test_s8b_binding_driftguards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_s8b_binding_driftguards.py:536), lines 536-537, `pytest-delegating`
  - [test_s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_s8b_holdout_freeze.py:1222), lines 1222-1223, `none`
  - [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_s8b_oracle_driver.py:4931), lines 4931-4932, `none`
  - [test_s8b_repo_scan_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_s8b_repo_scan_invariant.py:54), lines 54-55, `manual`

30 row, `release_condition`, production, env, CLI, docs は未変更です.

## 受理と拒否の差分

- 正規 pytest:
  - `pytest_configure` が session を mark.
  - module import を受理.
  - collection hook が従来どおり skip marker を 1 個付与.

- exact token:
  - module import と call-time wrapper の両方を受理.

- `python3` pytest-delegating runner:
  - `__main__` import を受理.
  - 直後の `pytest.main()` が canonical conftest enforcement を開始.

- manual/none runner, direct import, `--noconftest`:
  - token と active session が無ければ module import 時に prefix 付き拒否.
  - fixture 解決と `_run()` の helper scan へ到達しない.

- call-time wrapper:
  - exact token で import 後に token を外して直接呼ぶ経路を引き続き拒否.

## 実走結果

全投入が test process 起動前に次で停止しました.

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

| 対象 | 件数 | rc |
|---|---:|---:|
| `test_growth_test_holds_contract.py` 全件, 3 回投入 | collected 0, executed 0 | 16 |
| `test_plain_runner_coverage.py` 全件 | collected 0, executed 0 | 16 |
| `test_pytest_failure_digest.py` 全件 | collected 0, executed 0 | 16 |
| campaign held node, `--noconftest` | collected 0, executed 0 | 16 |
| env attestation direct runner を起動する contract node | collected 0, executed 0 | 16 |

queue state も ENA, STS, 待ち数, 実行数が観測不能でした. 指示どおり login node の直 pytest へ切り替えていません.

実施済みの軽量静的検査:

- `py_compile`, 3 file, rc=0.
- `git diff --check`, rc=0.
- AST runner 宣言照合, 8 module 全件 `errors=()`, rc=0.
- 作業木は上記 11 code/test file の変更のみ.

## 波及可能性

- active pytest 外で held module を introspection 目的に import していた caller は, exact token 無しでは新たに import refusal になります. これは指定された受理集合変更です.
- nested pytest と xdist は config identity ごとに mark され, inner session の unmark が outer session を消さない構造です.
- conftest コピー経路は新 public API の import 面が増えています. fallback は静的に維持していますが, `test_pytest_failure_digest.py` 未実走のため最終確認が必要です.
- plain runner の `__main__` 本体は変更していません.
- production の `orchestrator/campaign/` への波及はありません.

## 総括

F1-F3 のコードと検査は実装済みです. revB BLOCKER は親実測どおり closed, その他は dispatch rc=16 により実装済みかつ未実走のため partial です. docs 編集と commit は行っていません.