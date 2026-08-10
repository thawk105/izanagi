---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t721-source-closure
seq: 3
---

## 新規

### {{F:acceptance-lease-starves-on-prefetch-merge}}. 受入 lease の取り込み手順が待機時間の長い区画で飢餓し、取得した lease を捨てた [手順漏れ]

- 事象: 受入 lease を 24 分待って `acquired` を得たが、runbook 7.3 の
  「取り込みは親が事前に済ませ、待ち手は `git rev-list --count HEAD..main` が 0 であることの
  検査に留める」に従い、15 commit 遅れを検出して lease を返した。並行 wave が 4 本走る区画では
  待機中に必ず main が進むため、この手順は取るたびに捨てることになる。
- 根本原因: runbook 7.3 は「`acquired` の直後に local main を取り込んでから投入する」という
  **原理**を書きながら、その**機構**を「親が待ち始める前に済ませる」と規定していた。待ち時間が
  取り込みの鮮度を超える区画では原理と機構が両立しない。`--ff-only` を待ち手で使えないという
  既知の制約 (wave branch が自前 commit を持つと fast-forward できない) が、機構を親側へ
  寄せる誘因になっていた。
- 恒久対応: `docs/pegasus-runbook.md` 7.3 を是正し、**待ち手自身が `acquired` の直後に
  merge commit として取り込む** (message file を用意して `git commit -F`、`--no-edit` は使わない、
  競合時は `merge --abort` して lease を返す) と規定した。
- 再発検知: 待ち手 script が取り込み後に `git rev-list --count HEAD..main` を再検査し、
  0 でなければ受入を投入せず lease を返して非 0 で終わる (本 wave の
  `acceptance.sh` が実装。逐語は `output/insights/2026-08-10_t721-source-closure/`)。

## 再発

### F71

- **再発: 2026-08-10** — `tools/run_tests.py --collect-only` の**コンソール出力**から
  parameterized nodeid を採って変異 spec の期待 node にしたところ、8 件あるはずの case が
  5 件しか出ておらず、harness が「期待 node が pytest collection に実在しない」で fail-closed
  停止した。F71 根本原因 (2) と同じ「runner のコンソール出力は行前置と切り詰めを伴うため
  正本にならない」型で、consumer が harness ではなく spec 執筆へ移っただけである。
  件数は passed 数 (35 = 1 + 8 × 4 + 1 + 1) で照合して確定した。
