---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-28
wave: rulings-20260828-queue-policy
seq: 2
---

## {{D:queue-congestion-does-not-stop-submission}}. 他者のキュー混雑だけを Izanagi job の投入停止理由にしない

**決定:** 共有キューが利用可能なとき、他者の待ち job 数や混雑だけを理由に、Izanagi の task に
必要な job の投入を見送らない。scheduler の待ち行列へ通常どおり投入し、順番を待つ。

**理由:**

- 混雑を理由に Izanagi だけが投入を自粛すると、scheduler の公平な順番待ちへ参加できず、
  ユーザーの研究だけが進まない状態が続く。
- 待ち順と資源配分は scheduler が担う。キューが利用可能である限り、待ち数は投入禁止の意味を持たない。

**却下した選択肢:**

- 待ち job が多い間は投入しない — Izanagi だけが待ち行列へ入れず、進行不能が自己継続する。
- 混雑を避けるために必要以上の job を先回り投入する — 本裁定は必要な投入を認めるだけで、乱発を認めない。

**適用外:** キュー停止・利用不能、資源契約違反、task 固有の安全停止は従来どおり停止理由である。
