---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-04
wave: dev-wave-t2253-sort-grammar-cache-binding
seq: 3
---

## 再発

### F106

- **再発: 2026-09-04** — [T-2253] wave の段 6 fix 後、親が sort test file の単独走を投入した直後に、レビュー逐語を
  worktree の insight へ写した。runner は login node の bounded local を選び MemoryMax に当たったうえ、走行前後で
  tree の状態 (untracked の増加) が変わったため自動 fallback せず rc=16 で止まった。偽の赤ではなく fail-closed で止まり、
  実害は再走 1 回。根本原因は既存の再発と同じで、走行を待ち時間とみなして worktree 内で別段の作業を進めたこと。
  今回の新しい点は、受入全走・変異走行だけでなく runner の bounded local 経路も tree の前後照合を持つため、
  焦点走のような短い走行でも同じ型で止まることである。恒久対応は F106 のまま (投入から結果取得までは worktree を触らない)。
