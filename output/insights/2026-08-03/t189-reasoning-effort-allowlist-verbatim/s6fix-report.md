FX1〜FX6 をすべて実装しました。実装本体・docs・所有外ファイルは変更せず、commit も作成していません。

## 対応表

| Finding | 判定 | 対応 |
|---|---|---|
| FX1 | closed | spec と argv の負例を独立 node に分割 |
| FX2 | closed | 永続化 spec → load → argv 構築の E2E 負例を追加 |
| FX3 | closed | 面 2・3 の正例を独立したリテラル 5 値へ変更 |
| FX4 | closed | live launcher より前の membership assertion を削除 |
| FX5 | closed | 恒久対応の所有先 T-183 / T-184 を docstring に追記 |
| FX6 | closed | 通常 import と直接ロードの一致検査を追加 |

partial / regressed はありません。

## 編集ファイル

- [test_dev_waves_schema.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/orchestrator/tests/test_dev_waves_schema.py:271)
  - unknown effort の spec / argv 負例を別 node に分割。
  - 全許可値正例の入力をリテラル 5 値へ変更。
- [test_dev_waves_cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/orchestrator/tests/test_dev_waves_cli.py:150)
  - serve 正例の入力をリテラル 5 値へ変更。
- [test_dev_waves_worker.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/orchestrator/tests/test_dev_waves_worker.py:90)
  - `effort="none"` の永続化 spec を読み込み、child argv 構築まで流す負例を追加。
- [test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/orchestrator/tests/test_codex_worker_launch.py:554)
  - `_run_case()` より前の正本 membership assertion を削除。
- [test_effort_levels.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/orchestrator/tests/test_effort_levels.py:45)
  - 通常 import した両定数と直接ロード値の一致検査を追加。
- [effort_levels.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/tools/dev_waves/effort_levels.py:11)
  - model×reasoning 非対応組の恒久対応所有が T-183 / T-184 である旨を追記。

## FX2 の帰属根拠

追加テストは `build_child_argv(load_worker_spec(spec_path))` を呼びます。

- `load_worker_spec()` は永続化 bytes を読み、`parse_worker_spec()` に渡します：[worker.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/tools/dev_waves/worker.py:590)、[worker.py:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/tools/dev_waves/worker.py:592)
- `build_child_argv()` は child argv を構築し、`validate_child_argv()` を必ず呼びます：[worker.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/tools/dev_waves/worker.py:231)、[worker.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/tools/dev_waves/worker.py:246)
- 実 spawn 経路も同じ `build_child_argv()` を使用します：[worker.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-fix/tools/dev_waves/worker.py:394)

したがって次の帰属になります。

- `parse_worker_spec` membership だけを外す：load は通るが `validate_child_argv` が拒否するため期待どおり。
- `validate_child_argv` membership だけを外す：`parse_worker_spec` が load 時に拒否するため期待どおり。
- 両方を外す：例外なく argv が返り、テスト末尾の「受理してはならない」assertion だけが赤になる。

## 正本縮小時の期待赤

- FX3：`CLAUDE_EFFORTS` から `low` または `max` を消すと、`test_serve_accepts_every_allowed_effort` と `test_worker_spec_and_child_argv_accept_every_allowed_effort` が該当リテラル入力で赤になります。
- FX4：`CODEX_REASONING_EFFORTS` から `max` を消すと、`test_all_repo_policy_reasoning_values_are_accepted[max]` が `_run_case()` の subprocess 起動まで到達し、CLI の `invalid choice` により赤になります。

## runner と波及

CLI の `_run()` は追加更新不要でした。段 5 で追加済みの effort 2 関数が引き続き手列挙されています。schema・worker・effort_levels の plain runner は `test_*` を自動収集するため、分割・追加した関数も対象です。

所有外への静的な波及可能性は次のとおりです。

- FX1 の node 名変更に合わせ、親の mutation spec／期待 node 登録は再照準が必要です。
- worker の共有 `_spec()` は `effort="high"` を既定値として維持しており、既存 consumer の入力は変わりません。
- 通常 import テストは `tools.dev_waves` の package 初期化・解決不良も意図的に露出させます。
- docstring の bytes 変更により `_supervisor_digest()` は変わりますが、受理集合は変わりません。
- `conftest.py`、共有 fixture、実装本体、docs は変更していません。
- 作業開始時から存在した所有外の統合済み差分には触れていません。

pytest、plain runner、受入テストは実行していません。静的確認として、6 ファイルの AST 解析と差分・末尾空白検査だけを行いました。

## 総括

- 対応表要約：FX1〜FX6 は全 6 件 closed、partial / regressed は 0 件。
- 未解決点：fix 実装内にはなし。親による mutation node 再照準と計算ノード上の実測が未実施。