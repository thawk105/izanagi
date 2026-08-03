段 5・単位 C の実装を完了しました。指定外ファイル・docs は編集せず、commit も作成していません。

## 編集内容

- [tools/dev_waves/cli.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/cli.py:21)
  - `CLAUDE_EFFORTS` を import。
  - [serve の `--effort`:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/cli.py:93) に `choices=CLAUDE_EFFORTS` を追加。
  - `parse_server_profile()` と `SupervisorProfile` 利用箇所は未変更。

- [tools/dev_waves/schema.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/schema.py:16)
  - `CLAUDE_EFFORTS` を import。
  - [parse_worker_spec():802](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/schema.py:802) で `_EFFORT_RE` による形検査後、membership 違反を `INVALID_ARGS / {"label": "effort", "kind": "unknown"}` で拒否。
  - [validate_child_argv():858](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/schema.py:858) でも既存 `model-effort` 形検査後に同じ membership 検査を追加。
  - 新しい `ReasonCode`、生の不正値、schema JSON の変更はなし。

- [orchestrator/tests/test_dev_waves_cli.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/orchestrator/tests/test_dev_waves_cli.py:53)
  - serve の全必須 option を作る `_serve_args()` を追加。
  - `none` が `SystemExit(code=2)` と `invalid choice` で拒否される負例を追加。
  - `low / medium / high / xhigh / max` の全5値を table-driven parameterization で検査。
  - [手列挙 `_run()`:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/orchestrator/tests/test_dev_waves_cli.py:390) に新規2関数を登録済み。

- [orchestrator/tests/test_dev_waves_schema.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/orchestrator/tests/test_dev_waves_schema.py:234)
  - `_valid_argv()` を effort 指定可能にし、既存 WorkerSpec を `_valid_worker_spec()` へ抽出。既存期待値は維持。
  - spec・argv の `none` 拒否と exact detail を追加。
  - 全5許可値の spec round-trip と argv 検査を追加。
  - `HIGH` が spec 側で `kind="string"`、argv 側で `kind="model-effort"` のままになるP2保護を追加。
  - [同ファイルの `_run()`:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/orchestrator/tests/test_dev_waves_schema.py:359) は `globals()` の `test_*` 自動収集形式であり、個別登録不要と確認。

## 受理・拒否挙動

- 面2・serve CLI
  - 変更前: `--effort` は必須だが値域制限がなく、`none` を含む任意文字列を parse。
  - 変更後: `low / medium / high / xhigh / max` のみ parse。`none` は argparse の `invalid choice`、終了コード2。

- 面3・worker spec
  - 変更前: `_EFFORT_RE` に合う lowercase token は `none` も受理。`HIGH` は `kind="string"` で拒否。
  - 変更後: 全5許可値だけ受理。`none` は `kind="unknown"`、`HIGH` は従来どおり `kind="string"`。

- 面3・child argv
  - 変更前: `--effort=none` は形検査を通過。`--effort=HIGH` は `kind="model-effort"` で拒否。
  - 変更後: 全5許可値だけ受理。`none` は `kind="unknown"`、`HIGH` は従来どおり `kind="model-effort"`。

scope 外として、永続 profile の `parse_server_profile()` と [SupervisorProfile の ASCII 形検査:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/daemon.py:228) は従来どおりです。

## 所有外への静的波及可能性

- [tools/dev_waves.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves.py:12): `dev_waves serve` の実 entrypoint。新規 CLI 入力の受理集合が狭まる。
- [tools/dev_waves/daemon.py:1194](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/daemon.py:1194): profile から WorkerSpec を生成し、[build_child_argv():1225](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/daemon.py:1225) を呼ぶため、新 membership gate の影響を受ける。
- [tools/dev_waves/worker.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/worker.py:231): argv 構築後に `validate_child_argv()` を呼ぶ。
- [tools/dev_waves/worker.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/worker.py:590): spec 読込時に `parse_worker_spec()` を呼び、spawn 前に拒否する。
- [orchestrator/tests/test_dev_waves_worker.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/orchestrator/tests/test_dev_waves_worker.py:47): 共有 worker fixture は `high` のため受理集合内。[argv consumer:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/orchestrator/tests/test_dev_waves_worker.py:79) と spawn consumer が影響候補。
- [orchestrator/tests/test_dev_waves_integration.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/orchestrator/tests/test_dev_waves_integration.py:244): 統合 fixture は `low` のため受理集合内。real worker spawn を使う統合テスト群へ間接波及する。
- 新規 `_serve_args()`、`_valid_argv()`、`_valid_worker_spec()` は各所有テストファイル内だけの helper で、所有外の共有 fixture は変更していない。
- [schema.py の `__all__`:878](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u3/tools/dev_waves/schema.py:878) は未変更。`CLAUDE_EFFORTS` を schema API として再exportしていない。

## 静的確認

- `git diff --check`: 問題なし。
- 対象4ファイルの `python3 -m py_compile`: 構文エラーなし。
- pytest、plain-Python test runner、統合テストは一切実行していないため、緑とは報告しない。
- docs 編集・commit はなし。

## 総括

- 編集ファイル: `cli.py`、`schema.py`、CLI test、schema test の指定4ファイルのみ。
- 受理集合: 面2・3とも `low / medium / high / xhigh / max` に閉じ、`none` を拒否。
- `_run()`: CLI は新規2関数を手登録済み、schema は `globals()` 自動収集のため登録不要。
- 波及: daemon・worker・worker/integration consumer test へ静的な間接波及あり。所有外編集はなし。
- 未解決点: テスト実測は未実施であり、計算ノードでの dispatch は親の担当。