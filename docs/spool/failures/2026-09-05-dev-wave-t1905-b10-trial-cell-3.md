---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-05
wave: dev-wave-t1905-b10-trial-cell
seq: 3
---

## 新規

### {{F:duplicate-wave-artifact-root-moved}}. 同名 wave の並行起動で、後発 session が共有 artifact root を退避し先発の段 2 子を全損させた [手順漏れ] [セッション死・救出]

- 事象: 同じ [T-1905] 試し打ち wave が 2 つの背景 session で同時に起動した。後発 session は
  着手前に降りる判断をしたが、その直前に `dev-wave-jobs/<wave>/` (自分用に作った dir のつもり) を
  別名へ `mv` した。その瞬間、先発 session の段 2 codex 子 (plan) が同 dir を artifact root に
  使っており、launcher が `launcher diagnostics write failed: FileNotFoundError` で rc=2、
  成果物ゼロで終わった。後発 session は dir を元の path へ戻し、先発へ経緯を通知した。
- 根本原因: wave slug が artifact root の名前になるため、同名 wave は同じ dir を共有する。
  起動時に「同名の wave が既に走っていないか」を検査する手順が無く、後発が自分の dir と
  誤認して共有 dir を動かした。dev-wave 入口の起動手順にも「同名 wave の検査」は無い。
- 恒久対応: 後発 session が memory `duplicate-wave-launch-check-before-job-dir` を残した
  (job dir を作る前に `ListAgents`・`git worktree list`・`dev-wave-jobs/` で同名を検査し、
  後発が降りる。共有 dir を `mv` しない)。先発は同じ job-id の再利用を manifest が拒むため、
  新しい `--job-id` で段 2 を再投入して回復した (1 往復 = 約 10 分の損失)。
- 再発検知: wave 開始時に `dev-wave-jobs/<wave>/` が既に存在し manifest.json を持つなら、
  同名 wave が稼働中か直前に走ったと見なして停止する。段 2 子の rc=2 と `FileNotFoundError` の組は
  「起動していない」の合図であり、成果物の不在を子の失敗と読まない。

## supersede 追記

- F841 **supersede: 2026-09-05** — D1617 が (b) (driver に試し打ちの実行面を足す) を採り、後続 wave が `trial-cell` phase と balanced 45 セルの限定受理 (D1597 の形) を実装した。試し打ちの実行面は formal と別 campaign 同一性 (search_tag=trial + submission nonce) に置き、本走の driver bytes を共有したまま同一性束縛の外へ出した。
