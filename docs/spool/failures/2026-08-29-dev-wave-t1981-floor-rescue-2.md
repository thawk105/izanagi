---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t1981-floor-rescue
seq: 2
---

## 再発

### F270

- **再発: 2026-08-29** — 四度目。救出 wave で、対象 3 branch がいずれも `git merge-base
  --is-ancestor <branch> main` rc=0 だった。ancestry だけを読めば「全部着地済み、救出対象なし」で
  終わる形であり、`git cherry main <branch>` も全 commit を `-` にし、三点 diff
  `git diff main...<branch>` は空を返す。**しかし救出材料は commit ではなく worktree の未 commit
  差分であり、これら 3 手はいずれも構造的にそれを見ない。** 実際に 11 file 中 2 file
  (`orchestrator/tests/conftest.py`、`orchestrator/tests/test_real_repo_serialization.py`) は main
  未変更の実質的な差分を持っており、ancestry で打ち切っていれば中身を一度も見ずに捨てていた。
  F270 本体および 2026-08-16 の再発が挙げる反転手 (patch-id 照合、タスク ID での台帳検索) は
  どちらも commit を対象にするため、この面には効かない。族としては本体と同じ
  「安価に測れる量を状態の代わりに読む」で、今回は代理指標が ancestry である。
- 併記する実測: 判定を反転させたのは 1 手だった。**救出 file の追加行のうち、main の当該 file に
  1 行も存在しないものだけを残余として数える行単位照合。** 11 file・約 4100 行の差分が、残余
  0 行 (6 file)、数行 (3 file)、13 行 (2 file) に落ちた。読む対象が 4100 行から数十行になり、
  かつ「main が同じ内容を別の書き方で持っているだけ」の見かけの差分を自動的に外せた。
  なお残余ありの 3 file についても、内容を読むと main の後退 (旧名への改名、resume 再開支援の
  撤去、main の現行意味と逆を主張する試験) であり、行単位照合は着地判定の**入口**であって
  結論ではない — 残余が出た file は必ず中身を読む必要がある。
- 恒久対応: 新規の機械検査は本 wave では入れない。memory `three-dot-diff-is-not-unlanded-volume`
  と `cherry-plus-judged-by-content-not-path` に ancestry 面を追記し、救出 wave の入口で
  「branch が main の祖先でも worktree の未 commit 差分は残りうる」を先に確認する規律とする。
  lint 化の可否は F270 本体の恒久対応と同じく [T-1239] が持つ。
