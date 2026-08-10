実装済みです。変更は [test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2392) のみです。

変更した nodeid:

- `orchestrator/tests/test_env_contract_activation.py::test_issue_main_rejects_generation_skip_at_last_of_65_envs_without_publishing`
- `orchestrator/tests/test_env_contract_activation.py::test_issue_main_rejects_invalid_successor_at_last_of_65_changed_envs_without_publishing`
- `orchestrator/tests/test_env_contract_activation.py::test_issue_main_accepts_65_env_plus_one_and_publishes`

各 node で `ec.current_activation_state` を呼出記録付き spy に置換し、`finally` で `activation_state_calls == [None]` を検証します。`issuer` が別 module object を掴むと patched spy は呼ばれず記録が空のままなので、必ず赤になります。既存の実 authority 前後比較と `sys.path` 復元は維持しています。

静的検査:

```text
rg -n '(^|[^[:alnum:]_.])campaign\.env_contract(_activation)?([^[:alnum:]_.]|$)' \
  orchestrator/tests/test_env_contract_activation.py
rc=1、出力なし
```

旧 namespace の独立出現は編集対象から消えています。AST parse は成功しました。

焦点 4 node の実走を `tools/run_tests.py` 経由で試みましたが、`qstat -Q preflight rc=1` による Pegasus dispatch infrastructure failure（rc=16）で開始されませんでした。緑は主張しません。

## 総括

(a) namespace literal による `sys.modules` guard 3 件を、patched function の厳密な 1 回呼出 guard に置き換えました。

(b) 実装済み・pytest 未実走です。runner の dispatch infrastructure failure で停止しました。

(c) 親は上記 3 node、import-invariant node、続いて受入全走を再実行してください。