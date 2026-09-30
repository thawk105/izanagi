---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: worktree-md22-auditor-types
seq: 2
---

## 再発

### F819

- **再発: 2026-09-30** — gen-opt md_22 ([T-2890]) で 2 回。(1) 段 5 の実装子 2 本: 親が依頼文 `common-5.txt` を job dir へ `request-common-5.txt` と改名して複写し、依頼文の「同じ directory の common-5.txt を読め」に従った子が job dir で `common-5.txt` を探して即停止 (各約 70 秒、実装なし)。(2) 段 6 の review 2 本: 必読列挙の 1 行に「`<絶対 path>/probe/probe.py と author-probe-2.md`」と 2 file を並べ、子は 2 つ目を `probe/` 配下と読んで即停止。どちらも fail-closed で実害は再投入 1 往復ずつ。対処: 依頼文が相対名で参照する file は元の名前でも置く、必読列挙は 1 行 1 file の完全 path にする (以後の投げ文はこの形で通った)。型は既載の 2026-09-29 (near miss、「・」でつないだ 2 file) と同じ。
