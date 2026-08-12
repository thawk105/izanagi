## 総括

- 残る 1 件に対する免除述語の修正を実装した。
- 免除判定から `excluded_reason` を完全に除外した。
- 未測定 session の構造的な 5 条件を連言で固定した。
- 非空 throughput は常に証跡検査対象となる。
- M1／M2／M4／M12 は各 exact 1 件を静的確認した。
- 既存テストの期待値は一つも変更していない。
- pytest・変異 harness は未実走であり、状態は「実装済み・未実走」である。

変更箇所は [s8b_floor_stats.py:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_stats.py:447) の `_rep_evidence_exemption_kind` だけである。変更後の完全な免除条件は次の論理式になる。

```python
throughputs == []
and run_cmd is None
and session_median is None
and valid is False
and (
    exec_failures == reps_expected
    or (
        isinstance(probe_before, Mapping)
        and probe_before.get("competing") is True
        and probe_after is None
    )
)
```

`excluded_reason`、`rep_observations` の欠落、`rep_integrity_failures` の欠落は免除根拠に使用していない。したがって post-probe 競合によって理由が `competing_process` へ変わっても、全 rep の measure 例外という構造的事実から免除される。一方、`throughputs` が 1 本でもあれば先頭条件で必ず免除外となる。

[test_s8b_floor_stats.py:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/tests/test_s8b_floor_stats.py:490) の `test_verify_rejects_completed_measure_disguised_as_unmeasured_exemption` は未変更である。同攻撃は `exec_failures=0 != reps_expected=5` で、pre-probe skip の形にも一致しないため免除されず、空の `rep_observations` と `rep_integrity_failures=None` が引き続き拒否されることを静的確認した。

変異 anchor の静的件数は次のとおりである。

- M1 `if complete:`: exact 1 件
- M2 `throughputs, reps=self.reps`: exact 1 件
- M4 counter 完備資格条件: exact 1 件
- M12 `type(returncode) is int`: exact 1 件

`python3 -m py_compile orchestrator/campaign/s8b_floor_stats.py` と `git diff --check` は完了した。第 2 巡ではテストファイル、docs、`output/`、`s8b_holdout_freeze.py`、`test_s8b_approved.py` を編集せず、commit も作成していない。pytest、build、焦点テスト、変異 harness は一切実走しておらず、緑とは報告しない。