---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: dev-wave-t363-deadline
seq: 3
---

## 新規

### {{F:untrusted-run-latch-poisoning}}. 信頼できない観測が回復経路を潰す latch を作りかけた [恒真ゲート]

- 事象: [T-363] の段 5 実装で、実行予算の張り直しを「信頼できる (qstat rc=0 の) RUN 観測」に
  束縛する際、既存の `run_seen` latch を共用した。その結果、rc≠0 の qstat stdout に
  `Request State = RUN` が含まれるだけで `run_seen` が立ち、**その後に正常な rc=0 の RUN を
  観測しても張り直せない**状態が残った。塞いだはずの欠陥 (順番待ちが実行予算を削る) が、
  別経路でそのまま残る形だった。段 6 の敵対レビューが must-fix として摘出し、統合 commit 前に閉じた
- 根本原因: 「証拠の信頼性で gate する」新しい条件を、**別の意味を持つ既存 latch へ後付けした**。
  `run_seen` は「観測記録を 1 度だけ書く」ための latch であって「予算を張り直したか」ではない。
  gate を足すと latch の意味が 2 つになり、厳しい側の条件が緩い側の latch に食われた
- 恒久対応: 意味の異なる latch を分離する (`run_deadline_rebased` を新設)。回帰テストとして
  `orchestrator/tests/test_pegasus_dispatch_compute.py::test_trusted_run_after_nonzero_run_stdout_restarts_deadline`
  を置き、latch を `run_seen` へ戻す変異を事前登録して kill を実測した
- 再発検知: 上記 node と、変異 spec の `M5-latch-back-to-run-seen` (期待 KILLED)

### {{F:diagnostic-only-mutation-counted-as-kill}}. 受理集合を変えない変異を kill に数えかけた [恒真ゲート]

- 事象: 同 wave の変異事前登録で、`overall_grace_s` の項を落とす変異を KILLED として登録した。
  実際にはその変異が赤にするのは `state_history[-1].elapsed_s` が 4.0 → 3.0 になる診断値の差だけで、
  rc・qdel・`outcome` はいずれも変わらなかった。**受理集合が変わらない赤を耐性の証拠として
  数えることになり**、変異台帳の `KILLED` を 1 件過大計上する状態だった。段 6 の焦点再レビューが
  差し戻した
- 根本原因: 期待 kill テストを「その変異で赤くなるテスト」で選び、`DW-M03` が要求する
  「受理集合か fail-closed 挙動が期待方向へ変わったか」で選んでいなかった
- 恒久対応: 受理集合の差になる正例テスト
  (`orchestrator/tests/test_pegasus_dispatch_compute.py::test_overall_grace_allows_done_at_observed_run_deadline`)
  を追加し、当該変異の kill 根拠をそこへ移した。変異台帳には各 node が
  「受理集合の赤」か「診断だけの赤」かを区別して記録する
- 再発検知: 変異 spec の `M2-drop-overall-grace` の `expected_nodes` に上記正例が入っていること。
  焦点再レビューで「受理集合の赤 / 診断だけの赤」の区別を要求する
