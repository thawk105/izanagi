T-146 段5の実装を [test_dev_waves_integration.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1093) のみに行いました。commit・index操作・production・meta-test・docs・output artifact の編集はありません。

実装内容:

- literal `.s` と `socket → bind → chmod → capability-stat → listen` を維持。
- preexisting regular file / broken symlink を nofollow 観測し、`FileExistsError(EEXIST)` を送出。
- bind 例外後は `getsockname()` で ownership を判定し、helper-owned entry のみ回収。
- cleanup FNF は nofollow で不在確認できた場合のみ成功扱い。
- EPERM/EIO は元の型・errnoを維持して送出。
- unlink 成功後も pathname 不在を確認し、no-op unlink を拒否。
- hostile concurrent writer、close 例外族、production helper への一般化は行っていません。

Pre-fix control は 5 failed / 3 passed / 0 skipped でした。

- FAIL `...[partial-bind]`: helper-owned `.s` が残留。
- FAIL `...[fnf-after-real-unlink]`: cleanup 後の FNF が helper の `True` を上書き。
- FAIL `...[no-op-unlink]`: unlink の偽成功を受理し `.s` が残留。
- FAIL `...[regular-file]`
- FAIL `...[broken-symlink]`: preexisting entry を `False` に潰し、期待した `FileExistsError` を送出せず。
- PASS: `eperm`、`eio`、既存 `test_short_alias_bind_probe_separates_capability_loss_from_regression`。

実装後の実走結果:

- 新規2関数＋既存 T-138 gate: **8 passed / 0 skipped / 0 failed**
- isolation exactness meta-test: **1 passed / 0 skipped / 0 failed**
- long-path node: **0 passed / 0 skipped / 1 failed**
- 対象ファイル全体: **86 passed / 0 skipped / 1 failed**

long-path failureは、この workspace sandbox が実 AF_UNIX `bind()` に加え、未 bind socket の `getsockname()` も `EPERM` にするためです。ownership 観測不能を `False`／SKIPへ逃がさない契約どおり例外を送出しており、全体 green とは主張しません。

補助検査:

- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: rc=0
- Git index: 変更なし

静的波及:

- 所有外 caller: なし。helper の参照は対象ファイル内だけです。
- 共有 fixture: pytest共有 fixture はなし。`_PermissiveAliasSocket` を既存 T-138 gate と新規 matrix が共有。
- consumer test: 既存 T-138 gate、long-path roundtrip、ASTでmarkerを検査する isolation meta-test。
- production `tools/dev_waves/` への波及・変更なし。

最終 `git status --short`:

```text
 M orchestrator/tests/test_dev_waves_integration.py
?? output/insights/2026-07-29_t146-probe-cleanup-wave/
```

未追跡 output は開始時から存在した manager 所有物で、変更していません。

## 総括

指定1ファイルだけに helper fix と2関数・7 nodeの局所 matrixを実装し、新規 nodeは全件 PASS・SKIP 0、meta-testも PASS しました。唯一の未緑は sandbox が ownership 観測も拒否する long-path nodeであり、契約に従ってSKIP化せず失敗として報告します。