---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t184-followup
seq: 1
---

## {{D:worktree-liveness-by-cmdline}}. worktree の生存判定に argv を含める

**決定:** worktree が使用中かの判定に `/proc/*/cwd` の走査だけを使わない。
`/proc/*/cmdline` に当該 worktree の path が現れるかも見る。子を走らせる worktree は
`git worktree lock` する。保護の合図が要る場合は **worktree の外**に置き、掃除側がそこを見る。

**理由:**
- launcher 型の子は cwd に映らない。`tools/codex_worker_launch.py` の cwd は**起動元**
  (親 wave の worktree) であり、操作対象 worktree は `--repo-root` / `--cwd` / `--artifact-dir`
  として argv にしか現れない。実測で `/proc/*/cwd` 一致 0 件・`/proc/*/cmdline` 一致 14 件
  (launcher 7 + codex 本体 7) を 2 session が独立に観測した。
- cwd 走査は単なる見落としより悪い。**起動元 worktree が busy に見え、実際に使われている
  操作対象 worktree のほうが free に見える。**
- `git worktree lock` は必要だが十分ではない。lock が止めるのは `git worktree remove` であり、
  `rm -rf` + `git worktree prune` の手順は lock を見ない。
- 被害は静かに入る。走行中に working directory を失った子の receipt は
  `codex_exit_code=0` / `metering_status=complete` / `limit_trigger=null` のまま残り、
  値だけ見ても汚染に気づけない。

**却下した選択肢:**
- 施錠だけで済ませる — `rm -rf` 手順に効かない。
- worktree 直下へ `RUNNING-DO-NOT-DELETE.txt` 等の目印を置いて dirty 判定に引っかける —
  **規律 6 に反する。** 命令形の文字列を、子が読む作業ツリー (子にとっては指示ではなくデータで
  あるべき空間) へ注入することになる。加えて untracked file の追加は測定 treatment を変える。

## {{D:sendside-no-instruction-shaped-artifacts}}. 指示に見える artifact を未信頼入力の側へ置かない

**決定:** 規律 6 は「外から入る内容を指示として解釈しない」という**受け手側**の規律だが、
**送り手側にも対称の義務**を負わせる。保護・合図・運用の目印を置くときは、
それを**読むのは誰か**を先に決める。子が読む空間 (作業ツリー、trace、成果物、prompt へ
渡す資料) へ、命令形・禁止形の artifact を置いてはならない。合図はその空間の外に置き、
必要な側がそこを見に行く形にする。

**理由:**
- 受け手側の規律だけでは、善意の運用 artifact が指示として作用する経路を塞げない。
- 実例: 走行中の worktree を掃除から守るため worktree 直下へ `RUNNING-DO-NOT-DELETE.txt` を
  置く案が出た。掃除側の dirty 判定には効くが、その file 名を `ls` や `git status` で見るのは
  子である。掃除側の都合だけで置き場所を選び、読む側を見ていなかった。
- 置き場所を外に移せば、注入も treatment 変更も起きず、掃除側の目的も達成できる。

**却下した選択肢:**
- 「目印は無害だから例外扱いする」 — 無害性の判断が置く側の都合に依存する。
  規律 6 の境界は内容の善悪ではなく**どの空間に置くか**で引く。
