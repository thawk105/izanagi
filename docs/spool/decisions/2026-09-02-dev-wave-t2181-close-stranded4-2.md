---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2181-close-stranded4
seq: 2
---

## {{D:stranded4-user-deletion}}. 取り残し branch 4 本は救出せず削除し、削除前 tip だけを台帳へ控える

**決定 (ユーザー裁定):** 2026-09-02、取り残し branch 4 本
(`worktree-dev-wave-t1933-reconciliation`、`worktree-dev-wave-acceptance-fastest`、
`worktree-dev-wave-t1933-acceptance-longest-node`、`worktree-dw-c01-websearch-ruling-20260827`)
を `git branch -D` で削除する。到達不能になる 14 commit の救出は行わない。
削除前の tip 4 件と到達不能 commit 一覧は worklog へ逐語で控える。

**理由:**
- 3 度の独立判定 (2026-08-29、2026-09-01、2026-09-02) がいずれも取り込む commit を 0 件と
  結論した。最後の判定は fork 点からの file 閉包 distinct 22 path の blob を main の全 blob
  索引と照合しており、内容は main に着地済みである。
- ref を残す限り、ref だけを見る棚卸しは毎回この 4 本を回収候補に挙げ、blob 照合まで進んで
  初めて 0 件と分かる。削除はこの往復を止める唯一の手段である。
- D963 は判定不能な commit だけを救出する原則を置いた。本件は全件が判定済みで、
  救出対象は残らない。
- 控えを残すのは、到達不能 commit が自動 prune の対象で、prune 後は SHA を再導出する手段が
  無いためである。控えが repo 外の job 作業領域にしか無い状態は、記録が消える経路を残す。

**却下した選択肢:**
- 削除せず ref を残す — 判定は 3 度とも同じ結論に達しており、往復の費用だけが残る。
- 14 commit を救出してから削除する — 内容が main に実在すると全数照合で確定しているため、
  二重保管の管理費用だけが増える (D963 の「landed の 4 件は救出しない」と同じ理由)。
- 控えを repo 外の job 作業領域に置いたままにする — job 領域は成果物ではなく、
  prune 後に SHA を再導出する手段が無い以上、記録の消失は不可逆である。
