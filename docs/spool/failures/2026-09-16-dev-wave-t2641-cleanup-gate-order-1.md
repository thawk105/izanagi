---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2641-cleanup-gate-order
seq: 1
---

## 新規

### {{F:cleanup-status-writes-index}}. 掃除手順が命じる裸の `git status` が、同手順自身が禁じる index 書き換えを行っていた [恒真ゲート]

- 事象: `/cleanup-branches` §0 は「surviving worktree の tracked/untracked file・index・設定の
  作成/編集」を禁じるが、同 command §1 は全 worktree に対して裸の `git status --short` を命じていた。
  本 wave の親が実測したところ、tracked file の mtime を変えた直後に裸の `git status --short` を
  走らせると worktree の index の md5 が `622f9487ca7db6e31d7cab9adedbf62e` →
  `107713b4710d1cdbf74ffd6734743ec0` へ変化した。同条件で
  `GIT_OPTIONAL_LOCKS=0 git status --short` を走らせた場合は md5 が変化しなかった (負の対照)。
  つまり入口が、自分の禁止に反する命令を出していた。
- 根本原因: `git status` は stat cache が古いと index を書き戻す。掃除手順はこれを知らずに
  読み取り probe として扱っていた。同じ repo の `tools/check_branch_rescue.py` は子 git へ
  `GIT_OPTIONAL_LOCKS=0` を渡しており、対策は既に別経路に存在していた。
- 恒久対応: `.claude/commands/cleanup-branches.md` §1 で `GIT_OPTIONAL_LOCKS=0 git status --short`
  を明示する。
- 再発検知: 掃除実行後の §4 事後検査 (surviving worktree・index・repo file に新しい差分が無い)。
  index の bytes 不変までは §4 の status 比較では証明できないため、疑う場合は index の
  digest を直接取る。

### {{F:occupancy-checker-sees-reader-argv}}. 占有 checker が読み取り probe の argv を「占有」と数え、並列化が過剰な保持を生む [恒真ゲート]

- 事象: `tools/check_worktree_occupancy.py` は自分と checker 起動祖先を除く全 process の
  `/proc/<pid>/cmdline` を走査し、対象 path を argv に含むものを占有源 (`cmdline`) に数える
  (`_argv_matches_targets`)。`/cleanup-branches` §1 は各 worktree の `git status` を、
  §3 は「削除の直前に対象ごと」占有検査を命じるが、**両者の時間的関係を書いていなかった**。
  対象 path を argv に持つ読み取り (`git -C <wt> status`、
  `check_branch_rescue.py --retire-worktree <wt>`) を占有検査と並走させると rc1 になり、
  削除してよい worktree が「占有」として保持される。並列化の利得を打ち消す。
  同型は dev-wave 側でも既知で、wave 撤去が rc=21 になる原因と同じ機序である。
- 根本原因: checker は「対象を名指す process が生きている」ことを占有の証拠にする設計で、
  読み手の種別を区別しない。手順側に順序制約が無かった。
- 恒久対応: `.claude/commands/cleanup-branches.md` §1 に
  「読み取り・占有検査の起動親/wrapper (検査時も生存する親含む) の argv に対象 path 禁止」と
  「対象入り argv の全読み取り終了後に §3 の占有検査へ」を置く。
  checker 側は変更しない (読み手を無条件に無視させると占有検知そのものが弱まる)。
- 再発検知: 掃除で rc1 (占有) が想定外に多い場合、まず自分の読み取り probe と wrapper の
  argv を疑う。
