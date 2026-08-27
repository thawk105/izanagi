---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: rulings-20260828-queue-policy
seq: 1
title: 共有キューの混雑だけを Izanagi job の投入停止理由にしないと裁定した (docs のみ、branch worktree-rulings-20260828-queue-policy)
---

## 本文

- ユーザー裁定。共有キューが利用可能なとき、他者の待ち job 数や混雑だけを理由に、必要な
  Izanagi job の投入を見送らない。scheduler の待ち行列へ通常どおり投入して順番を待つ
  ({{D:queue-congestion-does-not-stop-submission}})。
- 発端は、裁定記録 branch の受入で 1 shard が `queue-wait-timeout` になった後、親が待ち数 49 を
  理由に再投入を保留したこと。ユーザーは「それでは自分だけ何もできない状態が続く」と指摘した。
  その判断を撤回した時点で、当該 branch は並行 session が main へ land・fold 済みだったため、
  重複する受入 job は投入していない。
- 並行 session への一次周知は repo 外の
  `rulings-inbox/2026-08-28-queue-congestion-is-not-submit-stop.md` と共有 handoff に置いた。
  session 間通信の可視範囲では直接送信可能な peer が 0 件だったため、直接 message は送れなかった。
- 本裁定は必要な投入を混雑だけで止めないという範囲に限る。不要な job の乱発、同一試行の無制限な
  再投入、キュー停止・利用不能や task 固有の安全停止の迂回は認めない。

## 次の一手差分
