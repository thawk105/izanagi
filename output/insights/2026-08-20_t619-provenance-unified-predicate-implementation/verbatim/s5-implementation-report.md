実装完了しました。編集は指定の2ファイルのみで、commit は作成していません。

- [tools/check_ai_provenance.py:1361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-unified-predicate/tools/check_ai_provenance.py:1361)
  - plain reachability、HEAD 固定・drift 検出
  - shallow/graft/replace・非一意 policy add の fail-fast
  - scope / implementation / CAB の統一述語
  - authoritative の明示配線、空 epoch/seed の非適用
  - T-619 台帳 entry の追加
- [orchestrator/tests/test_check_ai_provenance.py:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-unified-predicate/orchestrator/tests/test_check_ai_provenance.py:794)
  - side-branch fixture を scope-only / implementation-only に分離
  - authoritative oracle、repository guard、drift、台帳配線のテスト追加
  - docs byte 数 6102 の検証追加

変異確認は12項目すべて実施し、各変異に対応する単一理由のテスト失敗を確認後、実装を復元しました。

1. plain range: `test_default_commit_range_uses_plain_reachability_and_policy_prefix`
2. scope epoch: scope side-branch test
3. implementation epoch: implementation side-branch test
4. CAB seed: CAB side-branch test
5. HEAD drift: `test_authoritative_history_pins_head_once_and_rejects_drift`
6–8. shallow/graft/replace: 各 parametrized case
9. 非一意 policy add: `test_authoritative_repository_rejects_nonunique_policy_add`
10. ledger entry: `test_t619_known_violation_is_absorbed_in_authoritative_audit`
11. authoritative ledger wiring: `test_t619_authoritative_ledger_visibility_wiring_is_explicit`
12. explicit range の影響分離: `test_explicit_range_and_message_file_skip_authoritative_repository_guards`

検査結果:

- runner 経由の対象ファイル全体: `317 passed, 0 failed`
- `py_compile`、`git diff --check`: pass
- 通常の `tools/run_tests.py ...` は Pegasus の `qstat` preflight failure（child 未起動、rc=16）。同じ runner のローカル fallback で上記317件を実走。
- caller grep の結果、production 側の外部 caller は `main()` のみ。その他は同ファイル内の内部呼出しと対象テストのみ。
- `docs/ai-provenance.md` は親変更のまま 6102 bytes。docs は編集していません。

## 総括

T-619 の plan v2 と adjudication override に従った実装・テスト・変異確認を完了しました。