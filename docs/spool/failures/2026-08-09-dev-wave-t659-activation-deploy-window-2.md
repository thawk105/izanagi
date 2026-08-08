---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t659-activation-deploy-window
seq: 2
---

## 再発

### F24

- **再発: 2026-08-09** — 同型だが虚偽の度合いが一段深い形で、独立 10 例以上を実測した。
  背景タスクの完了通知が **producer の生存中に「完了 rc=0」を報告し、通知に載る Output 行が
  script の成功時 echo をなぞった文字列**だった (実 output ファイルは空、または不存在)。
  非 persistent な待ち手は偽完了で閉じられ、以後の実通知が来ない。`DW-O01` の
  「完了通知を判定にしない」が防壁として働き、**成果物の実在・`.done` の exit code・
  producer process の死の 3 点照合**で全例を看破した。恒久対応は既存の `DW-O01` で足りる —
  加えて待ち手は persistent 側で張り、偽完了を受けても kill も再 arm もしない (本 wave では
  偽完了を孤児と誤認して待ち手を 1 度落とした)。
