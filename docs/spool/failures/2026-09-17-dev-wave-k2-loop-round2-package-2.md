---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-k2-loop-round2-package
seq: 2
---

## 再発

### F333

- **再発: 2026-09-17** — docs-only wave (K2 ループ次巡の裁定パッケージ) の段 7 で、親が
  `check_ai_provenance.py` の全史監査を `timeout 200` で包んで起動した。この checker は既定で
  計算ノードへ dispatch するため、親が SIGTERM された時点で request `2730.nqsv` が孤児化し
  (`{"kind":"infra","reason":"signal-abort"}`)、wave worktree に `orphan-hold.json` と
  `orphan-holds/2730.nqsv.json` の 2 箇所が武装した。直後の再監査は
  `{"child_started":false,"kind":"infra","reason":"orphan-hold"}` rc=16。2026-08-23 / 08-24 と
  同型で、Bash tool 側の 120 秒自動背景化に加えて親が自前の `timeout` を重ねたのが直接原因。
  復旧は hold の `recovery` field どおり — qdel せず、`qstat` 一覧の行頭 RequestID で消滅を
  待ち、submission dir の終端証拠と tree clean / HEAD を確かめてから 2 箇所を job dir へ退避して
  削除した。dispatch 経路の command に呼び出し側 timeout を重ねない。
