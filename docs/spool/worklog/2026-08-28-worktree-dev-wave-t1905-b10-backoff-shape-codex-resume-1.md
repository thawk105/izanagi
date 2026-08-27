---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t1905-b10-backoff-shape-codex-resume
seq: 1
title: [T-1905] B-10 待ち方 grid は import 修理後の probe で物理残差 gate が発火し formal 前で停止した (コード + docs、branch worktree-dev-wave-t1905-b10-backoff-shape-codex-resume、変異 matrix = baseline PASSED・1/1 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 実装 commit `8df4fa25da01311e887336b6f454f6d33ec28a2c`。D95 Codex authorがcompute jobのmodule起動だけを実走済みの `-B -m` 規約へ揃えた。
- 敵対review 2本はtestのexact性不足1件で一致し、Codex fix後の直接退行を固定した。意図的なshell decoyへの完全防壁はscope外の限界として残した。
- 関連testはtarget 1 passed、B-10 file 55 passed。変異は `-I` 復帰1件を期待node完全一致でKILLした。
- probe request `953543.nqsv` はbnode142でdriver rc=0、18 cellを生成した。sourceは `8df4fa25d`、placeholder preregは `1549bd927`。
- 固定exclusive上限1.0%をbinaryの4 cellが超えた。最大は2 usの4.350306666666667%、他は5 us=2.307512761904755%、10 us=1.4950977142857091%、50 us=1.8777331238095178%。
- 規律2に従い上限を緩めず、§5はplaceholderのまま維持した。発効版、formal build、verify/perf、formal reportは生成していない。
- probe/receipt/job-resultの原bytesとdigestは `output/insights/2026-08-28_t1905-b10-backoff-shape-run/`。repo外durable rootも保持した。
- formal performanceの既存認可を実経路で確認する段には到達しなかった。

## 次の一手差分

### 更新

- [T-1905] **P1・probe関門で停止 → 再設計待ち**: import修理後の物理残差probeは18 cellを生成したが、事前登録済み1.0% exclusive上限をbinaryの4 cellが超えた。§5はplaceholderのまま、formalは未投入。上限を緩めず、probe結果を開示した新しい事前登録設計を先に決める。
  base: caa47b074300f8f5e1279f9733b892f6328f210ba25ba27318606affe7aa134c
