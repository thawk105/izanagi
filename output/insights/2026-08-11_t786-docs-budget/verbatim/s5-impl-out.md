## 総括

[tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/check_docs.py:3901) に次の検査を追加し、command guard へ結線しました。

```python
def _check_dev_wave_waiter_consumer_pins(
    dev_wave_text: str | None,
    core_text: str | None,
    operations_text: str | None,
    findings: list[str],
) -> None:
```

通る正例は、現行の command 段6・段9、`DW-C00`、`DW-O01` の逐語 pin と、symlink でない regular file の `tools/dev_wave_wait.py` です。

[テスト fixture と変異](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/orchestrator/tests/test_check_docs.py:46)も同期しました。production 定数から生成せず、手書きの独立 literal を使用しています。

- 検出ロジックを実装した変異: 9/9
  - `stage6-relocated`
  - `stage9-deleted`
  - `dw-c00-fenced`
  - `dw-o01-wrong-pid-source`
  - `target-symlinked`
  - `decoy-optional`
  - `decoy-negated`
  - `decoy-blockquoted`
  - `pre-wave-form`
- `decoy-optional` は同節の打消し語検査で拒否します。
- 実走による KILLED 確認: 0/9。全9件とも未実走であり、SURVIVED と判定したものもありません。

実走を試みた selector:

- `test_dev_wave_waiter_consumer_pins_accept_current_docs_contract`
- `test_command_guard_case_registration_is_complete`
- `test_command_docs_guard_positive_controls` の全 parameter

いずれも `tools/run_tests.py` が admission 予約台帳を更新できず dispatch を選択し、さらに `qstat -Q` が UID 認証エラーとなったため、テスト本体・collection 前に rc=16 で停止しました。したがって状態は明確に「実装済み・未実走」です。

実走できた検査:

- `python3 tools/check_docs.py` — 違反なし
- `python3 tools/check_codex_agents.py` — OK
- `git diff --check` — OK

裁定内の4 pinに取り零しは認識していません。明示的な scope 外として、runtime argv/receipt、runbook §7.3、SKILL.md、acceptance の `--owned-path`、producer の他の必須引数、`DW-C00` の実行時本数・再生成禁止は未検査です。また、打消し語は指定例を含む高信号語彙による構造検査であり、任意の言い換え全般を意味解析するものではありません。

docs は編集せず、commit も作成していません。