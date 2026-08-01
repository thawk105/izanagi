R8 の唯一の partial は静的に closed しました。

- 変更: [test_pegasus_test_dispatch.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_test_dispatch.py:1749)
- 追加: 6ケースの parameterized expected-red test
  - intent/result の欠落・重複
  - 順序逆転
  - matched candidate と submit/final ID の不一致
- 各ケースで実 `_validate_scheduler_lookup_chain` を呼び、exact reason を検証
- production 変更、commit、push なし

静的検査は Python 3.10 AST、pyflakes、全差分の各 diff-check が通過しました。

未実走: pytest、mutation harness、qsub/qstat/qdel、build、計算ノード受入。

## 総括

必須 pairing negative test の不足は解消済みです。未解決なのは指示どおり未実走の動的検証だけです。
