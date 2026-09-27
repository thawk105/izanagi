---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-27
wave: worktree-dev-wave-t2865-stage-f
seq: 3
---

## 新規

### {{F:auditor-role-output-vs-gate-schema}}. auditor role の出力節が driver の auditor gate の閉じた形を定めておらず、実 LLM の初回 E2E で proposal の読込みが止まった [手順漏れ]

- 事象: silo-function-policy 軸の段階 F の初回 E2E で、auditor (role `.claude/agents/auditor.md`) が `uncertainty` を文字列の配列、`nits` を文字列の配列、`proposed_tests` を独自の key で返した。driver の auditor gate (`orchestrator/campaign/auditor_gate.py` の `parse_auditor_dict`) は `uncertainty` を文字列 1 つ、`nits` を `{"finding"|"note": 文字列}`、`proposed_tests` をちょうど `{mutation, expected_gate, machine_judgment}` に限る閉じた形で、proposal の読込みが `AuditorGateFailure` で止まった。verdict (pass) と digest の echo は正しかった。
- 根本原因: role の出力節は field 名と意味だけを書き、gate が受理する型を書いていない。gate の型契約は fixture と test で固定されているが、LLM 子に渡る文面へ届いていなかった。段階 E までは auditor 出力を fixture で与えていたので表面化しなかった。
- 恒久対応: `docs/phase3-silo-policy-runbook.md` §1(d) に「spawn の prompt に gate の閉じた出力形を明記し、拒否されたら値を直さず同じ入力で再審査させる」手順を足した (本 wave の 2 回目の auditor はこの形で gate を通った)。role 本文の改訂はユーザー承認事項なので {{T:policy-axis-llm-fixed-texts}} に起票した。
- 再発検知: driver の `load_proposal_file` が auditor 出力を gate に通す時点の `AuditorGateFailure` (fails-closed。値の補正で迂回しない)。

## 再発

### F50

- **再発: 2026-09-27** — [T-2865] 段階 F の wave (背景 job + worktree 隔離) で、専用 handoff と開始 gate の log を背景 job harness の既定の job dir (`$CLAUDE_JOB_DIR` = home 配下の `~/.claude/jobs/<id>/`) に作り、wave の終盤 (受入待ち) に auto-memory `pegasus-keep-home-clean` を読んで気づいた (near-miss、実害なし)。/work の wave 用 job dir へ移し、home 側を消した。session の system prompt が一時物の置き場として `$CLAUDE_JOB_DIR/tmp` を名指し、`DW-O20` は「背景jobはrepo外」とだけ書くので、repo 外かつ home 外の具体的な置き場を開始時に決める手掛かりが入口に無かった。
