実装を完了しました。docs・単位 A/C 所有ファイル・commit には触れていません。

### 編集内容

- [tools/codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u2/tools/codex_worker_launch.py:41)
  - `CODEX_REASONING_EFFORTS` を E402 import 群へ追加。
  - `run --reasoning` に `choices=CODEX_REASONING_EFFORTS` を設定。
  - `check-receipt --expect-reasoning` と `_validate_receipt()` は変更なし。

- [orchestrator/tests/test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u2/orchestrator/tests/test_codex_worker_launch.py:332)
  - `_base_command()` にキーワード専用 `reasoning: str = "high"` を追加し、既存挙動を維持。
  - `none` が rc=2／`invalid choice` となり、receipt・manifest・PID/counter・artifact・output・Codex home が生成されない負例を追加。
  - `low / medium / high / xhigh / max` の全5値について、fake Codex の完全起動が rc=0 となり receipt の `reasoning` が一致する parameterize 正例を追加。
  - `_run()` は [pytest.main 委譲](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u2/orchestrator/tests/test_codex_worker_launch.py:1842)のため手動登録不要と確認。

### 受理・拒否挙動

変更前は、`run --reasoning` に値を指定すれば `none` など任意の文字列が argparse admission を通過していました。

変更後は `low / medium / high / xhigh / max` のみ受理し、`none`、`ultra`、`bogus` など集合外の値は child 起動前に rc=2 で拒否します。過去 receipt の読み取り・期待値照合の受理範囲は変更していません。

`none` は `_EFFORT_RE = [a-z][a-z0-9-]{0,31}` に一致するため形検査を通り、今回の負例は値域検査だけで拒否されます。

### 所有外への波及可能性

- tracked な実行コード内に launcher の直接 caller は見つかりませんでした。運用上の手動 caller が集合外 token を渡す場合のみ新たに拒否されます。
- 共有 helper の既存 caller は [同テスト:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u2/orchestrator/tests/test_codex_worker_launch.py:427)以下にあります。追加引数はキーワード専用かつ既定値 `"high"` のため、既存 caller は壊れません。
- receipt 関連 consumer の [tools/codex_worker_ledger.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u2/tools/codex_worker_ledger.py:443) と [test_codex_worker_ledger.py:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u2/orchestrator/tests/test_codex_worker_ledger.py:939) は、引き続き許可値を扱うため期待値への影響はありません。
- 単位 A の [test_effort_levels.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u2/orchestrator/tests/test_effort_levels.py:42) が正本の全5値を別途固定しています。

pytest は指示どおり走らせていません。`py_compile` による構文検査と `git diff --check` のみ実施し、異常はありませんでした。

## 総括

- 編集ファイル: `tools/codex_worker_launch.py`、`orchestrator/tests/test_codex_worker_launch.py` の2件。
- 受理集合の変化: 任意文字列から `low / medium / high / xhigh / max` の5値へ縮小。
- 波及の有無: 既存 helper caller は既定 `"high"` で不変、tracked な直接 caller なし。
- 未解決点: pytest 実測は親の計算ノード dispatch 待ち。実装上の既知未解決点なし。