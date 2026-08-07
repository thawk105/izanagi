実装は完了しました。docs・既存テスト期待値・commit/index には触れていません。

## 受理・拒否挙動

変更前:

- collector は既存 `--cwd-contains` の部分文字列一致を受理。
- `--cwd-under` は未定義のため拒否。
- 公開収集 API と wave artifact helper は未提供。

変更後:

- 既存 `--cwd-contains` の挙動は維持。
- 絶対 path の `--cwd-under` を追加し、`cwd == p` または `cwd.startswith(p + "/")` のみ受理。`<p>-fix` は拒否。
- `--cwd-contains` と併用した場合は AND。
- helper は project 1 個以上、絶対 `cwd-under`、絶対かつ repo 外の `out` のみ受理。
- collector 例外は `error`、model call 0 は `missing`、打切り・issue は `incomplete`。
- Pegasus login node は collector を呼ばず `blocked`。
- 既存出力、相対・repo 内出力、project 欠落は収集対象として拒否する一方、非 gate 契約により process rc は 0。

## 実装内容

- [claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:936)
  - `CollectionResult` と公開 `collect_report()` を抽出。
  - `main()` を render・stderr・rc adapter 化。
  - schema v2 と既存 CLI 出力を維持。
  - `--cwd-under` の絶対 path／境界一致を追加。

- [collect_wave_usage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:1)
  - import による collector 呼び出し。
  - 指定された status 優先順位と schema v1 envelope。
  - `os.link(tmp, out)` による atomic create-only publish。
  - 非 gate、login-node fail-closed、repo 外出力検証。

- [test_collect_wave_usage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:1)
  - M1〜M9、出力境界、issue、KeyboardInterrupt、親 directory 非作成を被覆。
  - 自走 `pytest.main` harness あり。

- [test_claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_claude_session_ledger.py:1347)
  - 公開 API と既存 JSON CLI の schema v2 parity test を追加。
  - 既存テストと期待値は変更なし。

## 検査

実装済み・未実走です。以下はすべて `tools/run_tests.py` 経由で試行しましたが、`qstat -Q preflight rc=1` により runner rc=16 となり、test process は起動されませんでした。

- `orchestrator/tests/test_collect_wave_usage.py` 全体
- `orchestrator/tests/test_claude_session_ledger.py::test_public_collect_report_matches_cli_json_schema_v2`
- `orchestrator/tests/test_plain_runner_coverage.py` 全体
- 上記三範囲の最終状態での合同再試行

`queue_state` も ENA・STS・待ち数・実行数を観測不能でした。規律に従い pytest の直接起動はしていません。

実施済みの静的検査:

- 対象 4 Python file の `ast.parse`: 成功
- `git diff --check`: 成功
- 99 文字超行検査: 該当なし
- docs／既存期待値の変更がないこと: 確認済み

## 静的な波及可能性

- 所有外 caller: 現行コード内に既存 production caller はなく、新 helper が唯一の新 callerです。親 docs の段 9 結線は未 land。
- 共有 fixture: `_load_ledger`、`_assistant`、`_write_jsonl` 等は変更していません。
- consumer test: collector 全体の既存 exact text、JSON、strict rc、read-only／bytecode test は refactor の影響候補です。未実走のため親の全走が必要です。
- meta consumer: `test_plain_runner_coverage.py` は新 test file の harness を検査しますが未実走です。

親 docs 未 land による許容 finding は次の二つだけです。

- `docs/dev-wave/core.md` の `DW-S09` 契約行欠落
- `docs/README.md` の production consumer／tool inventory 未更新

それ以外の赤は回帰として扱う必要があります。

## 総括

- 実装 file と行数:
  - `tools/claude_session_ledger.py`: 1,088 行、差分 `+69/-14`
  - `tools/collect_wave_usage.py`: 新規 229 行
  - `orchestrator/tests/test_claude_session_ledger.py`: 1,387 行、`+39`
  - `orchestrator/tests/test_collect_wave_usage.py`: 新規 409 行
- 検査結果: 構文・diff・静的境界検査は成功。pytest と meta-test は runner rc=16 のため未実走。
- 既知の穴: 親 docs 未 land、関連 test／meta-test／親受入全走が未実走。collector schema v2 を凍結したため `cwd_under` は ledger 内へ新 field を追加せず、wave artifact の `selector.cwd_under` に保持しています。