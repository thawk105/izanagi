---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2588-k2-loop-roundtrip
seq: 2
---

## 再発

### F723

- **再発: 2026-09-16** — [T-2588] で親が K2 role へ渡す知識源の逐語射影を省略記号で切った。
  切ったのは cmake の完全 path・`cv_history`・`rep_notes`・`run_cmd` の前置きで、測定値・genome・
  verdict は残っていた。**出力を読む前に子を停止し、全文で取り直したので成果物は汚れていない。**
  F723 との差は、今回の資料が `sha256` で束縛された知識源だったこと — 加工した射影を
  「解決済み manifest を渡した」と記録すると provenance が濁る。恒久対応 (a) の memory は
  読み込まれていたが、投げる直前ではなく投げた後に効いた。**prompt を組む手が長いほど、
  読みやすさのために切る誘因が働く。**
