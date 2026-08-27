## 対応表

| 所見 | 状態 | 理由 |
|---|---|---|
| F1 | closed | 同一 raw・正しい pin・active v1 holdout で正例と 9 負例を loader と differential 検査し、3 種の設計上の非対称も分離した。 |
| F2 | closed | CLI option、skeleton bytes、import 対象を exact allowlist 化し、環境変数による approver 補完の負例を追加した。 |
| F3 | closed | 既存 parser 拒否値に加え、parser を通過して canonical 再整形だけで拒否される node を追加した。 |
| F4 | closed | Linux では dangling symlink も `O_EXCL` が `EEXIST` を返すため、test 内で `O_EXCL` を無効化し、`O_NOFOLLOW` 単独の `ELOOP` を確認する node にした。 |
| F5 | closed | 成功経路と既存の parameterized 失敗経路で `tmp_path` 全体の前後 snapshot を比較するよう強化した。 |
| F6 | closed | differential の `[holdout-missing]` が、tool の caller IDs を candidate 部分集合へ差し替える変異だけで赤になる構造になった。 |

編集対象: [test_s8b_budget_approval_preflight.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1675-budget-approval-user-turn/orchestrator/tests/test_s8b_budget_approval_preflight.py:28)

## 足した node の一覧

```text
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_does_not_fill_empty_approver_from_environment
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_skeleton_rejects_dangling_symlink_leaf_via_nofollow_without_excl
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_accept_same_canonical_candidate
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_reject_same_contract_violation[approval-extra-key]
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_reject_same_contract_violation[scope]
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_reject_same_contract_violation[empty-approver]
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_reject_same_contract_violation[timestamp]
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_reject_same_contract_violation[budget-extra-key]
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_reject_same_contract_violation[oracle-shared]
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_reject_same_contract_violation[negative]
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_reject_same_contract_violation[negative-zero]
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_and_loader_reject_same_contract_violation[holdout-missing]
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_design_asymmetry_verify_does_not_enforce_authority_pin
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_design_asymmetry_verify_accepts_arbitrary_candidate_path
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_design_asymmetry_loader_uses_caller_holdout_ids
orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_rejects_noncanonical_timestamp_after_parser_accepts
```

全 parametrize ID が ASCII であることを静的確認済みです。

## 実走結果

実装済み・pytest 未実走です。

`python3 tools/run_tests.py orchestrator/tests/test_s8b_budget_approval_preflight.py -q` を実行しましたが、`qstat -Q preflight rc=1` により dispatch infrastructure failure、`rc=16` となり、子 process は起動しませんでした。collect-only の再試行も同じ結果でした。

静的確認:

- AST parse 成功
- timestamp probe: `2026-1-01T00:00:00Z` は parser 通過後、再整形結果と不一致
- symlink probe: `O_EXCL` は `EEXIST`、`O_NOFOLLOW` 単独は `ELOOP`
- whitespace error なし

## 波及可能性

- production tool、loader、README、docs は編集していない。
- 対象 test file は静的に 17 node から 33 node へ増加する。
- exact import allowlist により、将来の import 追加は意図的に review-required になる。
- F4 node は Linux/POSIX の `O_NOFOLLOW` と `ELOOP` 契約に依存する。
- runner の正規動作として `output/pegasus-dispatch/` に失敗 receipt が作成された。
- 親側で焦点 141 node と本 test file 33 node の再実走が必要。

## 総括

- 指定された F1〜F6 はすべて test file 内で閉じた。
- loader と verify の共通受理集合を正負両方向で直接接続した。
- pin、path、caller holdout authority は設計差として独立 node にした。
- N1 は文字列 denylist から exact surface 検査へ置き換えた。
- 無書き込み検査は candidate 周辺を含む `tmp_path` 全体へ拡張した。
- production の受理集合と既存期待値は変更していない。
- commit、add、branch 操作は行っていない。