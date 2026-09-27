---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-27
wave: worktree-dev-wave-t2853-fig15-input
seq: 2
---

## 再発

### F803

- **再発: 2026-09-27** — [T-2853] fig15 入力 wave の焦点走 1 回目で、親が wave worktree に未 commit で置いていた docs 編集 (`docs/paper-story/figures/README.md`・`tools/plotting/README.md`) を `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` が検出して 1 件赤になった (142 passed / 1 failed、Elapse 42 s)。assertion の左辺の余剰が docs の 2 path だけだったので実装差分に帰属させず、docs を記録 commit に入れた後の受入で再確認した。原因は (a) と同じで、作業ツリー全体を走査する検査の存在を焦点走の投入前に確かめなかった。焦点走は親の docs 編集を commit してから (または作業ツリーが clean の間に) 投げる。記録 = `output/insights/2026-09-27/t2853-fig15-input/README.md` §4。
