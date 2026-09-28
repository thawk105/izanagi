---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-cicada-verifier
seq: 3
---

## 新規

### {{F:attribution-sample-window-misses-witnesses}}. 壊し patch の帰属診断を先頭 N 件で打ち切り、判定器が報告する代表 witness と作りとして重ならなかった [変異帰属] [誤前提]

- 事象: 2026-09-29 の Cicada 正例の本走 1 回目 (一次資料 `output/insights/2026-09-29/vhash-cicada-verifier/README.md` §4) で、壊し 3 本とも non-serializable (巡回 7,766 / 1,292 / 2,279) だったのに、事前登録の帰属規則を満たす witness が 3 本とも 0 件で「検出したが帰属不能」になった。判定器は巡回 (SCC) のうち代表 20 件だけを witness として出し (`notes`: `N cycles (SCCs) found; reporting 20 witnesses`、走行の終盤の txid)、壊し patch は事象を thread あたり先頭 200 件 (走行の序盤) で打ち切っていた。帰属規則は変えず、事象を全件出すよう直して再走し、3 本とも代表 20 件中 20 件が帰属した。計算ノード 2 job 分と fix 1 巡を失った。成果物への影響なし (記録前)。
- 根本原因: 帰属を「判定器の witness と診断事象の突き合わせ」で設計したのに、判定器が witness を上限つきで選ぶことと、診断の標本窓がどこに落ちるかを突き合わせなかった。段 4 の事前登録で出力量を抑える上限 (200 件) を先に決め、上限と witness 選択の位置関係を検査しなかった。
- 恒久対応: memory `attribution-diagnostics-must-cover-verifier-witness-window` (帰属の診断は全件出すか、判定器の witness の txn から逆に引ける形にし、標本を打ち切るなら打ち切り窓が witness を含むことを事前に確かめる)。判定器の witness 上限は `orchestrator/verifier/` の既定で、変えていない。
- 再発検知: 帰属解析の自己検査に「witness の txn が事象列の後半にあるケース」を置く (今回の起動器の fix で足した、旧実装なら帰属 0・新実装なら 1 以上)。
