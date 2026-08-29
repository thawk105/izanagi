---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t1629-rescue-discard
seq: 3
---

## 再発

### F560

- **再発: 2026-08-29** — 救出依頼が「main へ一度も着地していない 7 file」という前提で来たが、
  実際には 6 file が `5107ced3c` で着地し `c986c1459` (merge) で撤去されていた。
  前提の裏取りに使った `git log --oneline --diff-filter=D --all -- <paths>` は 0 件を返す。
  path 限定 `git log` は既定で merge の差分を出さないため、**merge commit の中でだけ起きた
  削除は完全に不可視**であり、「削除 commit が無い」を「削除されていない」と読むと着地履歴を
  丸ごと取り違える。ここでは `git ls-tree` による tree 突合 (着地時点にあり main に無い) と
  `--ancestry-path` の 1 コミットずつの `cat-file -e` 走査で初めて撤去 merge に到達した。
  着地・撤去の有無は `--diff-filter` の出力ではなく **tree の内容**で判定する。
