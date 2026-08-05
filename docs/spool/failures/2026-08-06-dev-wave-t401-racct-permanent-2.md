---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t401-racct-permanent
seq: 2
---

## 再発

### F91

- **再発: 2026-08-06** — 段 1 brief で `_collect_accounting` の固定待ちを 8 秒と書いたが、
  内側の retry ループ (4 回 × 2 秒) だけを数え、それを包む `racctjob` / `racctreq` の 2 command
  ループを掛け落としていた。正しくは 16 秒で、同じ brief の (P3) は 16 秒と書いており本文内で
  矛盾していた。段 3 の 2 レンズが独立に指摘した。「関数を読んだ」を「呼び出し列を読んだ」と
  取り違える同じ型で、対象が cleanup 列からループの入れ子へ変わっただけである。brief 本文は
  書き換えず erratum で是正した (`output/insights/2026-08-06_t401-racct-permanent/brief-erratum-1.md` E1)。
