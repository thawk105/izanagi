---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2347-scr-worktree-land
seq: 3
---

## 再発

### F333

- **再発: 2026-09-07** — [T-2347] の焦点走で `tools/run_tests.py` が
  `rc=16` / `IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"orphan-hold"}`
  を返し、log の実体は `Pegasus orphan hold があるため scheduler command を起動しません` だった。
  **この再発が足す事実: 親を打ち切っていなくても同型になる。** 本件では `timeout` も手動の中断も
  無く、detached の 1 invocation が自分の qsub 窓で立った hold を見て戻っている
  (hold は `phase: "pending-qsub"` / `request_id: null`、job 名は `izdw-8101e58f94`)。
  既載の (i)〜(iii) はそのまま成立した — `qstat` には `980096.nqsv izdw-810 ... PRR` が生きており、
  job 終端とともに `orphan-hold.json` は機構自身が消え、提出 dir に `child_rc=0` の `result.json` と
  `311 passed, 1 skipped in 15.82s` の `<job>.o<id>` が残ったので再走は不要だった。
  親は手動 qdel をしていない。**`rc=16` を見た時点で走行を失敗と決めず、request ID を `qstat` で
  引き、終端後に提出 dir の成果物を読む。** 既存恒久対応に修正すべき新事実はない。

## supersede 追記

- F851 **supersede: 2026-09-07** — 恒久対応の「未実施」は解消した。案 (a) を {{D:fold-gate-absent-registration}} の形で実装済みで、`_registered_worktree_paths` は `FileNotFoundError` の登録を捨てずに未解決の絶対 path として残し、それ以外の解決失敗は従来どおり fail-closed とする。案として挙がっていた `prunable` marker での除外は実測 3 点により却下した。運用回避 (job が RUN の間は land を投げない) はもう要らない。
