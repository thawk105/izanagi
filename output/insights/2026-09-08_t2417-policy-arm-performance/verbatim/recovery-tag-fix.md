局所fixは実装済み・未実走です。

- [分析実装](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2417-recovery-author/orchestrator/campaign/backoff_policy_performance_analysis.py:842) の戻り値へ常時追加:
  - `headline_eligible: False`
  - `correctness_status: "uncertified"`
- [completeテスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2417-recovery-author/orchestrator/tests/test_backoff_policy_performance_analysis.py:453) と [空入力incompleteテスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2417-recovery-author/orchestrator/tests/test_backoff_policy_performance_analysis.py:1048) の双方で表示契約を確認。
- M16、M17はいずれも両テストのassertionで検出される構造です。
- 入力検証、数値、CI、仮説、version、prereg pin、順序、seed、欠測規則は未変更です。

静的確認:

- 2ファイルともAST構文確認成功
- `git diff --check` 成功
- diff内のU+0300〜U+036Fなし
- 変更は指定2ファイルの6行追加のみ
- pytest、`run_tests.py`、build、qsubは指示どおり未実走
- git add、commit、docs・JSON・台帳編集なし

所有外への波及:

- production caller: 直接参照なし。
- shared fixture: `conftest.py`などからの直接参照なし。
- consumer test: `orchestrator/tests/test_t2187_adaptive_const_probe.py`の5箇所が呼び出します。追加top-level keyのみなので静的には互換ですが、親側の焦点走対象です。
- meta-test: `acceptance_duration_ledger.json`とその検査群が対象テストfileのnodeidを扱います。テストの新設・改名はないため、本fix由来の台帳更新は不要です。

## 総括

| 判定 | 件数 | 内容 |
|---|---:|---|
| closed | 1 | complete／incomplete双方の集約結果が未認証を明示 |
| partial | 0 | なし |
| regressed | 0 | 静的確認上なし。ただし実走判定は親担当 |