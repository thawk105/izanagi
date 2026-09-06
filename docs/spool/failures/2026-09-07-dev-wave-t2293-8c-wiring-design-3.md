---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2293-8c-wiring-design
seq: 3
---

## 新規

### {{F:compute-scratch-worktree-registration-blocks-land}}. 計算ノード job が共有 repo へ登録した scratch worktree が、稼働中ずっと login 側の全 land を塞ぐ [手順漏れ]

- 事象: 受入緑 (tested_main = 現 main、tested_tip 4f163be3d) の land (2026-09-07 02:19 JST) が
  `rc=31 status=fold-gate-failed`、本文
  `fold gate failed: registered worktree path cannot be resolved: [Errno 2] No such file or directory: '/scr'`、
  `retryable_same_request=false`、`main_before == main_after` で止まった。`git worktree list` には
  `/scr/0_979578.nqsv-a5-second-boot-write-heavy/job-repo` と `/scr/0_979579.nqsv-a5-second-boot-balanced/job-repo`
  (detached、prunable) があり、両 job は `qstat` で RUN (経過上限 7200 秒、02:19 開始)。落ちた path は自分の wave でも
  login node 上の path でもない。
- 根本原因: `tools/pegasus/a5_second_boot_backoff_sweep.sh` が `git -C "$PBS_O_WORKDIR" worktree add --detach "$TMPDIR/job-repo"`
  で、計算ノードの node-local scratch を共有 repo の admin (`.git/worktrees`) へ登録する。登録は同 script が job 終了時に打つ
  `worktree remove --force` まで残り、login node からは path が存在しない。一方 `tools/dev_wave_land.py` の
  `_registered_worktree_paths` は全登録を `resolve(strict=True)` し、`OSError` を一律 `_FoldGateFailure`
  (`retryable_same_request=False`) にする。F672 と同じ経路だが、原因は EINTR (一時) でなく ENOENT (job が走る間ずっと持続) で、
  a5 sweep job が 1 本でも走っている間は repo 内の全 wave の land が fail-closed で落ち、緑の受入 1 本ごとに捨てられる。
  job script は「共有 repo の worktree として登録する」ことと、land は「登録は login node で解決できる」ことを
  互いに前提しており、その食い違いを検査する場所が無かった。
- 恒久対応: 未実施 (実装面、本 wave は docs のみ)。次 wave で (a) `_registered_worktree_paths` が prunable (path 不在) の
  登録を fold gate の非接触対象から除く、または (b) job script が共有 repo でなく job 専用 clone を使う、のどちらかを
  Codex author で入れる。それまでの運用は memory `land-discipline.md` の節
  「計算ノード scratch の worktree 登録は job 終了まで land を塞ぐ」(2026-09-07) に従う — land 前に
  `git worktree list` の `/scr/` 登録を見て、job が RUN の間は land を投げず、job 終了後に残った登録だけを
  `git worktree list --porcelain` の prunable 行が `/scr/` だけであることを確かめて prune し、受入を取り直す。
- 再発検知: land の `status=fold-gate-failed` の本文が `[Errno 2]` かつ path が `/scr/` で始まる。
  land 直前の `git worktree list` に `/scr/` 登録があれば本型の予兆。
