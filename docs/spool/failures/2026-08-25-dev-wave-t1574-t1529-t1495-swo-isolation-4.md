---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1574-t1529-t1495-swo-isolation
seq: 4
---

## 再発

### F480

- **再発: 2026-08-25** — 受入全走で
  `orchestrator/tests/test_pegasus_dispatch_compute.py::test_control_lock_allows_peer_after_pending_hold_is_durably_released`
  が **3 回連続で**赤になった (attempt 2 / 3 / 4)。破れたのは毎回
  `assert not first.is_alive() and not second.is_alive()` で、直前の `first.join(10)` が
  10 秒で戻りきらない。**同 node の単独走は 2 passed / rc=0 で緑**であり再現しない。
  本 wave の差分は dispatch / scheduler / pegasus のどの file にも触れていない
  (`git diff --name-only main...HEAD` で 0 件)。
  投入時は他 2〜3 wave が同時に受入全走を走らせていた。
- **今回わかったこと: 同一 wave 内で 3 回連続に出る。** 既存の再発記録はいずれも
  1 回の観測だったため「単発のフレーク」と読める形だったが、
  並行受入が続く時間帯では連続して出る。**「N 走一致なら flake でない」という
  一般則をこの族へそのまま当てると、非帰属の赤を自分の回帰と誤認する。**
  この族では回数でなく (a) 単独走の緑、(b) 差分の到達不能性、(c) 破れた assert が
  実時間の上界であること、の 3 点で判定する。
- 同族の別の現れ方も観測した。attempt 2 では
  `orchestrator/tests/test_real_repo_serialization.py::test_receipt_memo_real_xdist_order_has_no_worker_payer`
  が落ちたが、不変条件 (各 hook が 1 回ずつ・prewarm は controller・`prewarm-worker` 不在) は
  すべて成立し、`worker-hook` と `controller-hook` の**相対順序だけ**が反転していた
  (観測 trace = `['controller-hook', 'prewarm-controller', 'worker-hook', 'finish-controller']`)。
  実時間の上界ではなく**イベント順序**の assert だが、原因は同じ xdist スケジューリング遅延である。
  F480 の既存記述は wall-clock 上界に限定して読めるので、順序 assert も同族だと足しておく。
- 本 wave では当該テストの上界も順序 assert も変更しない。F480 が記すとおり
  所有者の設計判断であり、本 wave の scope 外である。
