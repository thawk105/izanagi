`DEV_WAVE_STAGE6_WAITER_CONSUMER_LINES` と正常系 fixture を更新しました。

写し元 [.claude/commands/dev-wave.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/.claude/commands/dev-wave.md:51>) の逐語は次の 3 行です。

```text
6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix、受入再走を行う。
   受入直前に受入 lease を `tools/dev_wave_wait.py acceptance` で `claim` し、
   `acquired` / `held-self` のときだけ投入する。
```

変更箇所:

- [tools/check_docs.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/check_docs.py:290>)
- [test_check_docs.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_check_docs.py:46>)
- `pre-wave-form` の旧逐語は拒否用の負例として維持。
- 項 9 の pin は変更せず、現物との byte exact 一致を確認済み。

検査結果:

- `python3 tools/run_tests.py orchestrator/tests/test_check_docs.py`: **rc=16**
  - `qstat -Q preflight rc=1` により dispatch 前停止。
  - 実行 nodeid: なし。
- 関連 nodeid 2 件の限定再試行も rc=16、未実走。
  - `test_dev_wave_waiter_consumer_pins_accept_current_docs_contract`
  - `test_command_docs_guard_positive_controls[pre-wave-form]`
- **実装済み・pytest 未実走**。緑は主張しません。
- `python3 tools/check_docs.py`: **rc=0**（`check_docs: 違反なし`）
- `git diff --check`: rc=0。

波及は `_check_dev_wave_waiter_consumer_pins` と、それを使う checker 本体・synthetic mutation tests に限定されます。作業中に親由来と思われる未追跡 `docs/spool/` 2 件が出現しましたが、触れていません。

## 総括

段 6 pin を `{acquired, held-self}` の現行逐語へ更新。  
項 9 pin は変更せず exact 一致を確認。  
docs checker は rc=0。  
pytest は環境起因 rc=16 のため未実走。