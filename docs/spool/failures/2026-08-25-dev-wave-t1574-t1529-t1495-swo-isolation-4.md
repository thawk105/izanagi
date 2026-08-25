---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1574-t1529-t1495-swo-isolation
seq: 4
---

## 再発

### F273

- **再発: 2026-08-25** — 受入全走を 2 回投入し、**2 回とも 2 件だけ赤になり、
  赤の中身が 2 回で完全に入れ替わった**。同時刻に他 2 wave が受入全走を走らせていた。
  1 回目は `test_ccbench_spawn_sites.py` の 2 件で、これは本 wave が新設した
  process 起動箇所の未登録であり**帰属する赤**だった (登録して閉じた)。
  2 回目は `test_pegasus_dispatch_compute.py::test_control_lock_allows_peer_after_pending_hold_is_durably_released`
  と `test_real_repo_serialization.py::test_receipt_memo_real_xdist_order_has_no_worker_payer` で、
  **どちらも本 wave の差分から到達しない**。
  前者は `assert (not True) where True = is_alive()` で、終了するはずの process が生きていた。
  後者は不変条件 (各 hook が 1 回ずつ・prewarm は controller・`prewarm-worker` 不在) が
  すべて成立したうえで `worker-hook` と `controller-hook` の**相対順序だけ**が反転した
  (観測 trace = `['controller-hook', 'prewarm-controller', 'worker-hook', 'finish-controller']`)。
  **2 件とも単独走で 2 passed。** 本 wave の `conftest.py` 差分は 1 行追加のみで、
  hook 配線にも xdist 順序にも触れていない。
- 今回わかった読み方: F273 の既存記述は「同じ file が大量に赤になる」形だったが、
  **少数の赤が走行ごとに別 node へ移る形**も同じ型として現れる。
  受入 lease は他 wave の受入走行を排除するが、**同時に走る他 wave の受入は排除できていない**
  (今回は 3 wave が同時に受入全走を走らせていた)。この隙間は F273 が記した
  「他 wave の codex 子を排除しない」隙間より広い。
- 帰属の判定に使った手順: `DW-O18` のとおり単独再走で再現性を測り、
  さらに assertion 本文を読んで「署名の見た目一致」でなく中身で判定した。
  加えて自分の差分が当該経路へ到達しうるかを `git diff main...HEAD` で確認した。
