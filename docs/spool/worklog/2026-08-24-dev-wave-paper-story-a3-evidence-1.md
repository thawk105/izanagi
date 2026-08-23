---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-paper-story-a3-evidence
seq: 1
title: paper-story A-3 の既存性能証拠を estimand 別に統合した
---

## 本文

- 新規性能計測を行わず、P2-4 の tracked profile/sweep/repro 成果物を再計算した。旧環境の論文採用値は、no-backoff stock-best比で write-heavy fixed 10us **+38.3%**、balanced fixed 5us **+11.3%** と確定した。
- profile **+38.5%** は CCBench commit、noinline計装、perf sampling、反復数が異なる機序診断値であり、+38.3%の丸め違いではない。D20どおりheadline不適格とした。repro **+42.2%/+11.7%** は別時刻・逆順で同方向だった定性的corroborationに限定し、平均していない。
- baselineはstock adaptiveでなく`BACK_OFF=0`のno-backoff stock-bestである。profileのexact measurement timestamp/compiler/binary digestは欠損のまま残し、worklog日付やcommit時刻から推測していない。
- 結論・条件表・source ledgerは `output/insights/2026-08-24_paper-story-a3-evidence-integration/README.md`。既存paper-story snapshot、凍結成果物、A-1 paired measurement、A-2 certificationは非編集・非所有とした。実装面変更なし、D95 author非発火、変異matrix免除。

## 次の一手差分
