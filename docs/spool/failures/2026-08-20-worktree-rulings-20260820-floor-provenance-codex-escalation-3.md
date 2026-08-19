---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: worktree-rulings-20260820-floor-provenance-codex-escalation
seq: 3
---

## supersede 追記

- F411 **supersede: 2026-08-20** — 恒久対応「停止を断定する前に…数分あけて1度だけ再投入する」の前提が崩れていたと判明した。ユーザーの開示により、レートリミット到達時にユーザー自身が手動でアカウント切り替えを行っていたケースがあり、見かけ上の「数分で自然回復した」はそれによる可能性が高い。恒久対応は{{D:codex-transient-death-escalate-not-wait}} (症状の即時検知とユーザーへの即時エスカレーション、自動再試行はしない) へ差し替える。
