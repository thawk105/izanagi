---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: dev-wave-t1940-b10-paper-figure
seq: 2
---

## 再発

### F618

- **再発: 2026-08-28** — 固定 commit の変異 matrix が全件完走した後、並行 session の main land により共有木事後検査が2回 rc=125。land lease取得後の同一matrix再走で閉じた。

### F619

- **再発: 2026-08-28** — collection timeout が result ledger 作成前に発生し、wrapper提示の `--resume` commandは既存`--out`必須で即停止。同型の正本どおり新scratch / outputのfresh走で復帰した。
