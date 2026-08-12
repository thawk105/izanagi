# §7.0 実行場所分類の実測 (rulings 第 7 束のユーザー委任、2026-08-13)

worklog fragment (branch worktree-rulings8-20260813、commit 8dbdadb7) の一次資料。
測定 job は gen_S へ qsub した 3 本。

| run dir | job | node | 対象 | 結果 |
|---|---|---|---|---|
| `run-0:908392.nqsv` | 908392 | bnode013 | ledger ×3, usage ×3 | ledger 有効 (delta +19.7/+11.6/+11.9 MiB, rc=2)。usage は --project 欠落で本体未走行 |
| `run2-0_908396.nqsv` | 908396 | bnode094 | 同上 | ledger 有効 (delta +18.1/負/+11.5 MiB)。usage は slug 先頭 - で SystemExit(2) |
| `run3-0_908401.nqsv` | 908401 | bnode094 | usage ×3 | 等号形でも内側 parser で同じ欠陥。実 slug では実行不能と確定 |

## 判定

- **claude_session_ledger.py (既定 argv `--json`) = local-ok 相当。**
  有効 5 走の charged delta 最大 20.6 MiB、margin 128 MiB 込み約 149 MiB < 規範値 512 MiB。
  入力 1.40 GB / 1,045 jsonl (既定は新しい 25 file)。
- **collect_wave_usage.py = 分類不能 (unknown 据置)。** tool 欠陥 (slug 先頭 `-` を内側
  parser へ渡せない + 失敗時 rc=0) の修正後に再測定。
- **mutation_worktree.py = 未測定 (意図的)。** 軽い複製への変更の実装後に測る。

## 方法論の注記

- login node では hooks/guard_bash.py が registry unknown の実行体を拒否する (正しい挙動、
  迂回していない)。計算ノードには per-job cgroup も cgroup delegation も無く
  (`/proc/self/cgroup` は `0::/system.slice/nqs-jsv.service` の 1 行のみ、2 ノードで確認)、
  runbook §7.0 の専有 scope 手順は非 root では実行できない。
- 採った方式は共有 service cgroup (`nqs-jsv.service`) の `memory.current` を busy sampling
  する delta 方式。同居 job の充当変動が混入する (実際に 1 走で delta が負になり無効化した)。
  registry へ反映する際は evidence にこの方法論の差を明記すること。

## 消してよいか

registry 反映 wave が evidence として参照し終えるまで残す。raw の peak/base/rc/stdout が
全走分ある。
