## 総括

実装済み・commitなし。pytest焦点走は Pegasus dispatch 障害により未実走です。

変更内容:

- [`auditor.md:66`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/.claude/agents/auditor.md:66): 型17〜21と具体的な file:line 機序を追加。
- [`auditor.md:89`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/.claude/agents/auditor.md:89): checklist 14を追加。D511文を66行・90行に二重配置。
- [`manifest.json:122`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/manifest.json:122): `maximum: 16 → 21`。
- [`review_ledger.py:17`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:17)、[`review_ledger.py:40`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:40)、[`review_ledger.py:86`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:86): 3 pinを更新。
- [`auditor_gate.py:29`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/auditor_gate.py:29): 受理範囲を1〜21へ拡張。
- [`test_auditor_gate.py:139`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/tests/test_auditor_gate.py:139): 型17〜21受理・型22拒否テストを追加。
- trigger共有テストを [`range(1, 22)`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1719) に更新。
- workload promptを [`1 through 21`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:298) に更新。

pin整合と `git diff --check` は緑です。

検査結果:

- `check_docs.py`: rc=0、違反なし。
- `check_codex_agents.py`: rc=1。理由は想定どおり未再生成の `.codex/role-adapters/auditor.json` byte-parity driftのみ。
- 指定pytest 6対象はすべて `qstat -Q preflight rc=1` / `dispatch-no-child`、pytest child未起動。したがって各々 `0 passed / 0 failed / 0 skipped`、nodeid範囲なし（実装済み・未実走）。

CC側の `coder_effect_gate.py` と `sort_swo_oracle.py` は着手前後で無変更です。`auditor_gate.py` は sort / trigger-gating 両軸で共有されるため、型17〜21が両軸から引用可能になりました。

親編集済みの `docs/phase3-s5-sort-runbook.md` は保持し、docs・coder role・`.codex` は編集していません。