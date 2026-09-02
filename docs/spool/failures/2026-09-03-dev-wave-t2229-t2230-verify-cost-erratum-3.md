---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2229-t2230-verify-cost-erratum
seq: 3
---

## 再発

### F333

- **再発: 2026-09-03** — T-2229 / T-2230 wave の受入で、親が受入全走
  (`tools/dev_wave_wait.py acceptance -- python3 tools/run_tests.py`) を前景で投げ、
  **Bash tool の上限である 10 分**で打ち切られた (rc=143)。shard job `969417.nqsv`
  (`izdw-shard-0`) が孤児化し、`output/pegasus-dispatch/orphan-hold.json` が
  `job-may-remain-without-terminal-evidence` で武装した。2 回あとに投入した受入は
  `stage=acceptance-command rc=70 source_rc=16 reason=dispatch-attestation-missing` で止まり、
  子 log の実体は `acceptance shard gate failed: dispatch-infrastructure` で、
  **テストは 1 件も走っていない。** 既載の型どおりだが、次の 1 点が台帳と食い違う。
  **恒久対応の 2 択のうち片方が、受入全走では選べない。** 既存記述は
  「長時間走りうる検査は余裕あるタイムアウト、または背景経路で起動する」と書くが、
  Bash tool の前景タイムアウトは**上限が 10 分**で、並行 wave が走る条件下の受入全走は
  それを超える。**受入全走に前景経路は存在せず、背景投入が唯一の経路である。**
  過去の再発は 2 分の既定や `timeout 3000` という書き手が選んだ値が引き金だったのに対し、
  本件は**上限まで上げても足りなかった**点が違う。
  復旧は既載の契約どおりで新事実は無い — 手動 qdel をせず (F47 型ラッチを立てないため)、
  `qstat` の出力本文で request の不在 (`Batch Request: 969417.nqsv does not exist on nqsv.`)
  を確認し、source が clean で HEAD 不変であることを確かめてから
  `orphan-hold.json` と `orphan-holds/969417.nqsv.json` の 2 file を手動削除した。
  作業ツリーへの被害はゼロ (tracked 差分・HEAD とも不変)。
