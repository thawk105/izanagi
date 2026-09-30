---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-lock-order-axis
seq: 2
---

## 再発

### F1078

- **再発: 2026-09-30** — dev-wave-lock-order-axis の fix 子 (fix-f-2) の終了直後 13:29 JST に、子木の gitdir `.git/worktrees/lock-order-f/index.lock` が 0 byte で残った。起動器は残差を commit できていた (cf50faedd) が、続く待ち手の `--commit-worktree` が rc=70 `worktree-commit failed reason=add-all`、同じ木で後から起動した 2 つの子 (変異準備・件数の fix) の起動器の終端 commit も rc=3 で同じ理由で落ち、成果は未 commit のまま木に残った (親が所有 path 限定の diff で取り出した)。親が F 木を cmdline・cwd に持つ process が 0 件であることを確かめて lock を消した。同じ wave の他の子木 3 本には lock は無かった。lock を作った process は未特定 (2 例目、どちらも同じ producer の終端 commit の直後)。

### F26

- **再発: 2026-09-30** — dev-wave-lock-order-axis の fix 用子木の `git worktree add -b` が checkout の途中で「cannot create directory …: システムコール割り込み」(EINTR) により rc=128 で終了し、作りかけの木は消えて branch だけが残った。既存 branch を指定した `git worktree add <path> <branch>` の単独の再実行で成功した。
