---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: dev-wave-t244-p3-redesign
seq: 3
---

## 再発

### F37

- **再発: 2026-08-04** — 親が `run_tests.py ... | tail` で dispatch を投げ、pipeline rc (=tail) を
  見て緑と誤読しかけた。dispatch の `result.json` の `child_rc=1` を突き合わせて実測前に検出し、
  偽緑の記録には至っていない (near miss)。以後の受入・変異走行は rc をパイプに通さず
  ファイルへ直接取得した。
