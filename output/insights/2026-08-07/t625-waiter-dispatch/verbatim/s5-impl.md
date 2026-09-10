実装済みです。commit・git add・docs 配下の編集は行っていません。

### 受理・拒否挙動

編集前は key `24` が入口・契約の双方になく、欠落状態を受理していました。入口だけに `24` を追加すると契約外 key として拒否される状態でした。

変更後は `24 → docs/dev-wave/core.md:DW-C00` を受理し、`24` の欠落または参照先の誤配線を拒否します。発火条件セルの文言は従来どおり checker の比較対象外で、受理集合をそれ以上変更していません。

### 変更内容

- [.claude/commands/dev-wave.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:106): 裁定の逐語行を追加。
- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:505): 条件 `24` の契約を追加。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4328): mutation 分岐・case 集合・needle の3箇所へ登録。non-operations key `{15,21,22,24}` の外延と参照先を literal で固定する pin test も追加。

### 実走結果

- `python3 tools/check_docs.py`: rc=0、違反0件。
- `python3 tools/check_codex_agents.py`: rc=0。
- Python構文検査と `git diff --check`: rc=0。
- 入口実測: 9056 B、最長137文字。上限9500 B／140文字以内。
- `python3 tools/run_tests.py orchestrator/tests/test_check_docs.py -q`: collection前にrc=16。sandbox上でlocal admission台帳がread-only、compute dispatchも`qstat -Q`失敗のため、実行0件。

未実走nodeidは `test_non_operation_condition_contract_pins_exact_targets`、`test_command_docs_guard_positive_controls[condition_waiter_deleted]`、および同ファイル全体です。変異matrix・親の受入全走も未実走です。

波及可能性は、契約から自動生成されるsynthetic fixture、parametrizeされたguard case collection、`dev_wave_land.py`・`task_run_check.py`等のcheck_docs caller、dev-wave Skill/dispatcher consumerです。operations集合とその19件期待値は不変です。

## 総括

- 入口へ条件24の裁定逐語行を追加した。  
- check_docs契約へ`24 → DW-C00`を追加した。  
- guard caseを3箇所登録し、non-operations literal pinを新設した。  
- check_docs・Codex契約・構文・diff検査は緑、入口は9056 B／137文字。  
- pytestはinfra rc=16で0件、実装済み・未実走。  
- docs変更・commit・git addはなく、親の全走と変異検査が残る。