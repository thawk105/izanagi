---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2320-backoff-sweep-gate-layer2
seq: 3
---

## 再発

### F251

- **再発: 2026-09-07** — 掃除主体が並行 session でなく**兄弟 job の終了処理**である型。同じ detached
  `submit-tree` から A-5 2 job と T-2266 tail 3 job を同時に走らせたところ、先に終わった A-5 write-heavy
  job の cleanup (`tools/pegasus/a5_second_boot_backoff_sweep.sh` の `git worktree prune --expire now`) が、
  5 job が共有する submodule gitdir (`…/.git/worktrees/<submit-tree>/modules/external/ccbench/worktrees/`)
  上の他 job の worktree 登録を消した。各 job の ccbench worktree はノードローカル `/scr/<jobid>-…/` にあり、
  別ノードから見ると存在しないので prune が「消えた worktree」として削除する。2 秒後に A-5 balanced と
  T-2266 3 job が同時に `git status` / `git worktree list` rc=128 (`fatal: not a git repository`) で落ちた
  (A-5 balanced は 8 genome の commit 後、T-2266 は 8 点中 6 / 6 / 4 点の commit 後)。関門も計測も無傷で、
  失った値は無い (T-2266 は A-5 無しで再投入)。**A-5 投入器は同じ checkout から 2 job を出すので、
  後に終わる job が必ずこの経路で落ちる構造**であり、09-02 / 09-04 は関門で先に落ちていたため顕在化しなかった。
  対応は裁定へ返した (投入器を checkout ごとに分けるか、job 本体の prune を自 path の remove に限定するか。
  いずれも登録簿と F660 に触れる)。判別 = 同一 checkout の gitdir を共有する job が複数走るとき、
  どれか 1 本でも `worktree prune` を打つなら他は生きていても落ちる。記録は
  `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md` §5。
