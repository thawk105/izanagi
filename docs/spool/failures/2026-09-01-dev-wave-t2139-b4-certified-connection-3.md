---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t2139-b4-certified-connection
seq: 3
---

## 再発

### F206

- **再発: 2026-09-01** — 今度は手動の incoming gate ではなく、受入待ち手が claim 後に回す
  `merge-history-provenance` 段で同型が出た。wave 側 worktree が base で止まっている間に
  main 側が既知違反 entry を 1 件足しており、古い checker がそれを
  `known provenance violation data index-only member does not match HEAD` として
  実行不能と報告して rc=70 になった。**F206 の再発検知手順どおり incoming 側を見れば足りる** —
  当該 entry は `git cat-file -e main:tools/known_violations/<name>.json` で実在し、
  wave 側 HEAD にだけ無かった。実装差分とは無関係な非帰属赤である。`DW-O20` の
  「HEAD 差は `--ff-only` で揃える」に従って解消し、取り込み後の full 監査は同じ木で
  rc=0 (7454 件、新規違反なし) になった。**恒久対応は増やさない** — 既存の `DW-O20` と
  F206 の再発検知手順で説明でき、待ち手側の gate は設計どおり fail-closed に働いている。
