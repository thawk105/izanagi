---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: worktree-dev-wave-ccbench-cicada-bugfix
seq: 2
---

## 再発

### F819

- **再発: 2026-09-29 (near miss)** — md_19 (CCBench Cicada の build 不具合の修理) の段 6 レビュー B の投げ文が、必読射影の 1 行に「`<絶対 path>/out/s5-author-A.md・probe_syntax.log`」と 2 file を「・」でつないで書き、子は 2 つ目を直前の path の directory (`out/`) 相対と読んで読めず、「読めなければ即停止」どおり 3 attempt とも停止した (出力 71 byte、model call わずか)。全 path を 1 行 1 絶対 path に直した B2 で受理された。以後の投げ文 (fix 2 本・焦点 2 本・検証 script のレビュー 2 本) は 1 行 1 絶対 path で書き、同型は出なかった。T-2854 の段 6 (2026-09-27) と同じ型で、どちらも fail-closed で安く止まった。
