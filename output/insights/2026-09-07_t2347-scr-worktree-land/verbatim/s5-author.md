## 総括

裁定どおり実装しました。`prunable` marker・record 分割・prune は導入せず、`resolve(strict=True)` の `FileNotFoundError` だけを受理します。

T1〜T10 も追加済みですが、runner の計算ノード dispatch が失敗したため、状態は**実装済み・pytest 未実走**です。commit は作成していません。

## 実装した差分 (file:line と要旨)

- [tools/dev_wave_land.py:3449](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2347-author/tools/dev_wave_land.py:3449)
  - `FileNotFoundError` の場合のみ未解決の絶対 path を保持。
  - その他の `OSError` / `UnicodeError` は従来の `_FoldGateFailure`。
  - 行走査、空判定、overlap 判定、`_execute_fold_gate` は不変。
- [test_dev_wave_land.py:392](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2347-author/orchestrator/tests/test_dev_wave_land.py:392)
  - 本物の `git worktree add`、porcelain、admin directory を扱う補助 helper を追加。
- [test_dev_wave_land.py:9045](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2347-author/orchestrator/tests/test_dev_wave_land.py:9045)
  - T1〜T8：第三の実在 worktree、path 不在、`.git` のみ欠落、改行 path、Permission/Unicode、空一覧、registry 永続、TOCTOU overlap。
- [test_dev_wave_land.py:9341](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2347-author/orchestrator/tests/test_dev_wave_land.py:9341)
  - T9：path 不在登録を残した実 `land()` が `landed`。
- [test_dev_wave_land.py:9357](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2347-author/orchestrator/tests/test_dev_wave_land.py:9357)
  - T10：T9 と同じ setup に wave dirt だけを加え、現行どおり `(RC_DIRT, "rejected")` を期待。

既存テストの期待値変更・削除・skip はありません。docs、job script、他 tool、registry は未変更です。

## 実走した検査 (nodeid・範囲・結果)

pytest nodeid の実走は 0 件です。代わりに以下の静的検査を実走しました。

- AST parse：変更 2 ファイル、rc=0。
- T1〜T10 定義・重複検査：10/10 unique、rc=0。
- `git diff --check`：変更 2 ファイル、rc=0。
- production 全体の `prunable` / `worktree prune` / record 分割検索：該当なし。
- 変更ファイル：指定された 2 ファイルのみ。

## 実装前の現行挙動 (受理・拒否)

- 受理：全 `worktree ` path が decode と `resolve(strict=True)` に成功し、隔離 directory と重ならない場合。
- 拒否：
  - path 不在も含む全 `OSError` / `UnicodeError` → `_FoldGateFailure`、land では rc=31 / `fold-gate-failed`。
  - `worktree ` 行ゼロ → `registered worktree list is empty`。
  - 実在登録との overlap → `_FoldGateFailure`。
  - landing wave の dirt → rc=20 / `rejected`。
- 今回広げた受理集合は「path 不在登録を捨てず、絶対 path のまま overlap 比較へ進める」一点だけです。

## 波及可能性の静的列挙

- production の直接 consumer は `_execute_fold_gate` のみで、`_run_fold_gate`、`land()`、CLI caller へ間接波及します。
- 既存 consumer test：
  - `test_fold_gate_exports_full_tree_applies_raw_bytes_and_runs_one_pytest`
  - `test_fold_gate_missing_junit_reports_bounded_escaped_child_output`
  - `test_fold_gate_real_argv_environment_create_junit_in_gitless_tree`
  - `test_fold_gate_tmp_isolation_preserves_main_and_wave_status_bytes`
- 共有 fixture `_git`、`_Repo`、`_repo` は変更せず再利用しました。
- 制約 meta-test 候補は `test_pytest_collection_config.py`（収集・命名）と `test_fold_gate_nodes_contract.py`（registry）。
- scope 外の他 worktree tool、locked 一般化、bind mount、job clone、残骸掃除には波及させていません。

## 未実走・未了

- T1〜T10、既存 consumer nodeid、上記 meta-test、変更 test file 全体は未実走です。
- `tools/run_tests.py` は全指定、単一 nodeid、`-n 0`、collect-only の全試行で、`qstat -Q preflight rc=1`、`child_started=false`、rc=16。テスト子は一度も起動していません。
- queue-state も ENA / STS とも観測不能でした。
- したがって pytest 緑・closed とは申告しません。実装面は完了、検証面は環境復旧後の実走待ちです。