---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2486-ssh-cgroup-equivalence
seq: 1
title: [T-2486] 遠隔検査の ssh session は rank と別の cgroup object に入る — ただし per-job の cgroup 境界はどちらの側にも無かった (docs + 実測、branch worktree-dev-wave-t2486-ssh-cgroup-equivalence、実装面の repo 差分ゼロにつき変異 matrix 免除)
---

## 本文

- **依頼の枠組みより広い答えが出た。** 依頼は「rank **終了後**の ssh session」を問うたが、
  rank が生きているノードへの ssh でも、head 自身への折り返しでも同じく別 cgroup object だった。
  rank の終了は、観測された membership 差の必要条件ではない。
- **より重い事実は、per-job の cgroup 境界が rank 側にも無いことだった。** rank が入るのは
  per-job cgroup ではなく node ごとの共有 NQSV service cgroup で、cpuset と task affinity は
  どちらの側も全 48 CPU である。したがって「ssh だから割当の資源保証を失った」ではない。
- **段 3 の敵対相談が親 brief の前提を 1 件倒した。** 親は brief に「`gen_S` は 1 node 専有」と
  書いたが、runbook §1 は `Exclusive submit = OFF` で「専有はスケジューラが保証するものではない」と
  実測記述している。親も投入前に独立に同じ誤りへ気づき正誤表を書いていた。両者は独立に一致した。
- **段 6 のレビューが親の結論の誤りを 4 件見つけ、すべて現物で裏が取れた。** (1) 「memory だけが
  非対称」は偽で `pids.max` も非対称。(2) 「祖先まで全部 `max`」は偽で root の `memory.max` は
  `ABSENT`。(3) 「per-job の CPU 資源境界が存在しない」は採取範囲より強い — `cpu.max` を採っておらず、
  `qstat -f` には `(Per-Job) CPU Number = Max: 48` が実在する。(4) 「欠落した観測点 0 件」は偽で、
  ssh の remote stdout・`qstat` の採取時刻・投入前 `qstat -Q` が durable な記録に残っていない。
  **4 件とも記述を狭めて直し、欠落は再測定せず欠落として明記した。**
- **既存実測の再現と新規を分けた。** 非 head rank の `0::/system.slice/nqs-jsv.service` は
  runbook §7.0 の 2026-08-13 実測 (2 ノード) の再現であり新発見ではない。同節が併記する
  cgroup delegation の不在は本 probe が採取しておらず、「再現した」とは書かない。
- **probe は Codex `role=author` 子に書かせた。** [T-317] (dev-wave の凍結境界が repo 外の
  使い捨て probe に及ぶか) は `docs/decisions.md` に無く未裁定であり、command 本文の凍結境界は
  所在を限定せずに「実行可能な probe / harness / script」を実装面としている。重い側に倒した。
  probe は repo へ入れず wave job dir に置き、worktree は clean のまま保った。
- 親の手順ミス 2 件。**worktree の checkout に `timeout 300` を掛けて SIGTERM で殺した** —
  負荷 53 のログインノードでは 22,955 file の checkout が 5 分を超える。さらに rc を `tail` へ
  通していたため rc=143 を 0 と誤読した (`check-rc-not-through-pipe` の型)。
  **`tools/dev_wave_submodule_init.py` の内部 timeout は 30 秒固定**
  (`tools/dev_waves/git_state.py`) で、同じ負荷では初回が必ず落ちる。同じ argv を timeout 無しで
  温めてから再実行して通した。
- 工数: codex 子 3 本 (consult 1 / author 1 / review 1、いずれも `gpt-5.6-sol`)。
  実装子は `tools/run_tests.py` を実走できず「実装済み・未実走」で戻した。probe の投入・実走・
  検算はすべて親が行った。

## 次の一手差分

### 完了

- [T-2486] request `986762.nqsv` (3 ノード) で rank 側と ssh 側の cgroup・cpuset・affinity を
  同一 job 内で突き合わせた。ssh session は rank とは別の cgroup object (systemd の login session
  scope) に入り、それは rank の終了とは無関係だった。per-job の cgroup 境界はどちらの側にも無い。
  結果は `output/insights/2026-09-09_t2486-ssh-cgroup-equivalence/README.md`、機体固有の事実は
  `docs/pegasus-runbook.md` §1、先行 insight §8-2 には追記した。
  remaining: none
  base: 821706c126610d4356b008b631dca95d4438d61810b928023adc3a7a7292268e

### 新規

- {{T:fanout-remote-membership-acceptance}} **P2・ユーザー裁定待ち**: 遠隔検査の受理条件に
  資源文脈の同値性を含めるか。[T-2486] の実測では観測した 3 経路すべてが exact な membership
  同値性を満たさなかったので、そのまま受理条件にするとどの経路も通らない。先行 insight
  `output/insights/2026-09-09_t2457-a6-fanout-live/README.md` §9 が挙げた問いと同じものである。
- {{T:fanout-remote-memory-cap}} **P3・新規**: 遠隔 worker が memory 上限の外にいることを扱うか。
  [T-2486] の実測で、rank 側は共有 NQSV service cgroup の `memory.max = 123480309760` の下に
  あるが、ssh 側は leaf から `user.slice` まで有限値を持たない。`pids.max` は逆向きに非対称である。
