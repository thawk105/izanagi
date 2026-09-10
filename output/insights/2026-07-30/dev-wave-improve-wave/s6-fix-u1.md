所有2ファイルの current bytes を修正しました。commit / push はしていません。

変更ファイル:

- [tools/pegasus_policy.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u1/tools/pegasus_policy.py)
- [test_pegasus_policy.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u1/orchestrator/tests/test_pegasus_policy.py)

所見別の状態:

1. unrelated host + non-NQSV PBS: **closed**
   - `OTHER` として分類し、raw PBS値を保持。NQSV、Pegasus domain、`pegasus*` / `bnode*` はfail-closed。
2. affinity APIなしのfallback: **closed**
   - 明確な`OTHER`だけ`os.cpu_count()`相当へfallback。
   - Pegasus-like、bnode、NQSV uncertaintyではfallbackを呼ばない。
3. `-n auto/logical`: **closed（U1 API）/ partial（統合）**
   - `OTHER`ではsymbolic値を保持、computeではaffinity上限へ解決、整数`0`はserialを維持。
   - U2所有の`tools/run_tests.py`がsymbolic値をpolicyへ渡す統合配線は別途確認が必要。
4. 公開API名: **closed**
   - `test_default_workers` / `test_default_jobs`を廃止し、`default_pytest_workers`へ変更。
   - `test_*`公開callableがないことを固定するtestを追加。
5. regression / positive control: **closed（実装）/ partial（実走証拠）**
   - affinity API欠落の実分岐、CPU-count到達、fail-closed側でfallback未到達、symbolic値、公開名を直接検査するtestを追加。

静的確認済み:

- Python 3.10.12による両ファイルのAST解析
- isolated modeでの`pegasus_policy` import
- `git diff --check`
- 変更パスが所有2ファイルだけであること

未実走:

- pytest、plain test runner、F42 meta-test
- build、qsub、live PBS、mutation、acceptance
- login node実走禁止に従い、greenは主張しません。

残risk:

- U2 callerが`auto/logical`を整数変換前にpolicyへ渡す必要があります。
- sandbox上の共有`.git`がread-onlyだったためindex更新に失敗し、状態は2ファイルとも`AM`です。indexには段5版、worktreeに今回の修正版があります。親は`git diff HEAD -- <所有2パス>`で採取するか、writableな管理面で再度`git add`してください。

## 総括

U1所有範囲の実装は完了しています。end-to-endの確定には、U2 caller配線の統合とcompute node上での対象test・meta-test・mutation・acceptance実走が必要です。
