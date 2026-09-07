---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t1281-qsub-waiter
seq: 3
---

## 新規

### {{F:hang-mutation-orphan-hold}}. hang 変異を dispatch へ投げると job が walltime まで居座り orphan-hold で wave が止まる [手順漏れ] [資源競合]

- 事象: 変異本走 (`--runner-mode dispatch`) の 11 件目で、待ち手の引数検査を外す変異が
  計算ノード job の中でハングした。harness の `hang_timeout_seconds` (300 秒) は job を止められず、
  job は自身の walltime (3,600 秒) まで実行し続けた。harness は終端証拠を取れずに orphan-hold
  (request 982386.nqsv) を立てて中止し、**変異を当てたまま作業ツリーを残した**。
  手動 `qdel` はユーザー手番の掛け金を武装させるため使えず、job の walltime 満了まで
  約 45 分、ツリーの復元も受入も land も進められなかった。
- 根本原因: 変異対象が「待ち手の deadline を守る引数検査」だったため、外した結果が赤ではなく
  **既定 6 時間の待機**になった。local runner なら probe の per-mutation timeout で観測できるが、
  dispatch では harness が子 job を kill できないので、DW-M06 が言う「超過は orphan hold 中止 +
  変異残留」がそのまま起きる。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M06` (hang 変異は `hang_risk` と timeout へ隔離し、
  timeout を fail-open の証拠とする。dispatch は `hang_timeout_seconds` < job walltime) が既に
  正本である。本 wave はこれに従い、**待ち手自身の待機時間を伸ばす型の変異を dispatch 本走から
  外し**、login 自走 probe の hang 観測を erratum として台帳へ残す運用を採った。
  復旧手順は `output/pegasus-dispatch/orphan-hold.json` の `recovery` field が正本で、
  対象の不在または終端を `qstat` の本文で確認 → `git checkout --` で dirty path を復元 →
  clean と HEAD を確認 → hold と sidecar を削除、の順に行う。
- 再発検知: 変異 spec を書く時点で「外すと待ち手の待機時間が伸びる述語か」を確かめる。
  該当するものは login 自走 probe で hang を観測して `expected_status: TIMEOUT` として記録し、
  dispatch の本走 spec には入れない。probe は per-mutation timeout と `try/finally` の復元を持ち、
  各回の前後で `git status --porcelain` が空であることを確かめる
  (`output/insights/2026-09-08_t1281-compute-waiter/evidence/probe-nodes.json` が実測)。
