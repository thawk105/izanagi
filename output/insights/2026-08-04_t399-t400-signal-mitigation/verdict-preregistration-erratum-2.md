# 事前登録 erratum 2 — mitigation 安全終端の機械指標の訂正 (2026-08-05)

- `authority: none`
- `default_effect: no-state-change`
- 本文書は `verdict-preregistration.md` の erratum である。初回凍結文は消さない。

## 対象

捕捉可能性判定の mitigation 条件 4 「終端が正常終了 (walltime kill でない) —
qwait rc=0 側の安全終端契約」。

## 実測が示した誤り

条件 4 の**実体** (walltime kill でない自発終了) は変えない。誤っていたのは
「自発終了なら qwait rc=0」という**操作化の仮定**である。実測 (a1、request 887918):

- scheduler `.e`: `%NQSV(INFO): Batch job received signal SIGTERM. (Exceeded per-req
  elapse time limit)` — **SIGKILL ではなく SIGTERM** (警告 signal の配送記録)
- 会計 block: `Elapse: 134S / Remaining Elapse: 46S` — **上限 180 秒の 46 秒前に終了** =
  自発終了 (D139 の危険側対照: t362-default は `Elapse: 184S / Remaining: 0S`)
- それでも **qwait は rc=9 を返した** — NQSV は elapse 警告 signal を送った request に対し、
  自発終了でも rc=9 を報告する

## 訂正後の機械指標 (条件 4 の操作化)

「walltime kill でない自発終了」は次の連言で判定する (qwait rc の値は判定に使わない):

1. scheduler `.e` の signal 行が **SIGTERM** (警告) であり **SIGKILL でない**
2. 同 block の **Remaining Elapse > 0** (上限前の終了)
3. Python parent の `finally_exit` event が存在する (cleanup 完走)

危険側 (捕捉不能) の判定は凍結どおり: scheduler 明示 **SIGKILL** + 3 層無受信 +
canary `MUTATED` (D139 と同型、Remaining Elapse: 0S)。

## 判定への影響

条件 1〜3 (SIGTERM 受信・束縛・cleanup + readback) は不変。条件 4 の実体も不変で、
操作化だけをスケジューラ自身の出力に基づいて訂正する。UNKNOWN 規約・grace の読み方・
十分性式は不変。
