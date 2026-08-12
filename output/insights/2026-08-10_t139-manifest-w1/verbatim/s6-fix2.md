修正しました。

- [test_t139_preregistration_binding.py:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:577)
  - s7 の `new_text` を承認予定の逐語＋LF（117 bytes）に固定。
  - s15 と s7 の locator は `[2, 4, 4]` とし、4 行目だけ重複。
  - 期待 composed 行も同じ exact bytes に更新。
- `erratum.py`、docs、他テストの期待値は変更していません。commit もしていません。
- production の operation 数、出現数、対象行 SHA-256、`old_text` bytes、1 行制約、exact digest 検査はすべて未変更です。

検証結果:

- production probe: s15/s7 の全 validator 通過後、`LocatorOverlapError` のみ送出
- exact digest: 一致（117 bytes）
- `check_codex_agents.py`: rc=0
- `check_docs.py`: rc=0
- `git diff --check`: rc=0
- pytest node: dispatch infrastructure failure（`qstat -Q` preflight、rc=16）のため未実走

## 総括

**実装済み・未実走**です。静的検査と production probe では、locator 重複だけが拒否理由として残ることを確認済みです。