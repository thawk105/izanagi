## 総括

4 件の must-fix はすべて `closed` として実装した。  
standalone 起動相当の import と K=3 注入を runtime probe で確認した。  
pytest は wrapper が計算ノード dispatch を選び、queue preflight rc=1 で child 未起動のため未実走。  
変更は waiter と指定された 2 test file の計 3 file、未 stage・未 commit である。

## 所見ごとの対応表

| 所見 | 状態 | 変更箇所 |
|---|---|---|
| must-fix 1: standalone import 不発 | `closed` | [tools/dev_wave_wait.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:24)、[test_dev_wave_wait.py:3385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3385) |
| must-fix 2: queue 不可時の fallback 消失 | `closed` | [tools/dev_wave_wait.py:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:821)、[test_dev_wave_wait.py:3483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3483) |
| must-fix 3: 空文字で無効化 | `closed` | [tools/dev_wave_wait.py:824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:824)、[test_dev_wave_wait.py:3452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3452) |
| must-fix 4: literal `"3"` と cross-contract | `closed` | [test_dev_wave_wait.py:3364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3364)、[test_run_tests_shards.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_run_tests_shards.py:177) |

## 変更した file と関数

- [tools/dev_wave_wait.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:24)
  - `__file__` から repo root を解決し、house 作法どおり `sys.path` 先頭へ追加。
  - `_acceptance_launcher_environment()` を変更。
  - queue が具体的に `ENA=ENA`、`STS=ACT` と観測された場合だけ注入。
  - False、例外、契約外、観測不能の fail-open 結果では注入しない。
  - 環境値が厳密な `""` の場合だけ未指定として扱う。

- [orchestrator/tests/test_dev_wave_wait.py:3297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3297)
  - launcher 捕捉 helper に queue 観測 seam を追加。
  - standalone subprocess、空文字、queue 正負例を追加。
  - K の期待値を literal `"3"` へ固定。

- [orchestrator/tests/test_run_tests_shards.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_run_tests_shards.py:177)
  - waiter、parser、effective K を結ぶ cross-contract test を追加。

## 追加・変更したテスト

- `orchestrator/tests/test_dev_wave_wait.py::test_pegasus_login_acceptance_launcher_adds_three_shards_only`
  - expected を production 定数ではなく literal `"3"` に固定。

- `orchestrator/tests/test_dev_wave_wait.py::test_standalone_waiter_sys_path_resolves_shard_injection`
  - subprocess の初期 `sys.path[0]` を `<repo>/tools` に固定。
  - cwd、repo root、test file directory を初期 `sys.path` から除外。
  - production bootstrap 後の import と literal `"3"` 注入を検査。

- `orchestrator/tests/test_dev_wave_wait.py::test_empty_acceptance_shard_request_is_injected`

- `orchestrator/tests/test_dev_wave_wait.py::test_acceptance_launcher_queue_not_confirmed_keeps_inherited_environment[unavailable]`

- `... [exception]`

- `... [contract-drift]`

- `... [observation-unavailable-fail-open]`

- `orchestrator/tests/test_run_tests_shards.py::test_waiter_three_shard_cross_contract_is_eligible`
  - waiter 定数 `== "3"`。
  - parser 結果 `== 3`。
  - 適格条件下の effective K `== 3`。
  - expected 側に production 定数を使用していない。

## 実走結果

pytest 焦点走は2回試行した。

1. 追加契約テスト群: nodeid selector 5、pytest 実行 0 件、passed 0 / failed 0 / skipped 0。wrapper rc=16、`qstat -Q preflight rc=1`、child 未起動。

2. 指定2 fileと consumer群: file selector 2、consumer nodeid 6、pytest 実行 0 件、passed 0 / failed 0 / skipped 0。同じく wrapper rc=16、child 未起動。

したがって pytest は「実装済み・未実走」であり、緑とは報告しない。

代替検証:

- standalone import・注入 runtime probe: 1/1 passed。
- queue、空文字、cross-contract runtime probe: 1/1 passed。
- 変更3 fileの AST parse、結合文字検査、`git diff --check`: passed。
- 受入全走: 未投入。

## 波及可能性の静的列挙

- waiter 起動時に repo root が `sys.path` 先頭へ入る。standalone 起動でも repo-local `orchestrator` を解決できる。
- queue reason の形式が将来変わった場合、注入は fail-closed で停止し、従来の runner admission 経路へ戻る。
- 非 Pegasus、明示された非空 shard 値、site/queue 例外では従来どおり `env=` を渡さない。
- launcher argv、receipt projection、collection、選択 node、除外、保留処理は変更していない。
- 静的 consumer として waiter本体、shard contract、land E2E、resume boundary、fold contract、docs/startup consumerを特定したが、pytest は未実走。

## 破らなかったことの確認

- `tools/run_tests.py` は編集していない。
- `tools/acceptance_launcher.py` は編集していない。
- `orchestrator/tests/conftest.py` と `tools/acceptance_shards.py` は編集していない。
- `docs/` 配下は編集していない。
- `git add`、`git commit` は実行していない。index 差分は空。
- pre-stage 5 の既存期待値を変更、反転、緩和、skip、削除していない。段5追加分の expected だけ指示どおり literal 化した。
- 受理集合、選択 node、恒久除外、保留適用は変更していない。
- 新しい環境変数、CLI flag、設定 file は追加していない。
- nit・情報所見には手を広げていない。
- 受入全走は投入していない。