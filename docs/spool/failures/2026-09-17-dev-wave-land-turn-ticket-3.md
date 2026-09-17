---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-land-turn-ticket
seq: 3
---

## 新規

### {{F:land-storm-lock-busy}}. 8〜13 本の land が共通 flock の再取得競走で全員 lock-busy になり 76 分着地ゼロになった [資源競合] [観測]

- 事象: 2026-09-16 21:09〜22:25、並行 dev-wave 8〜13 本の land が全員 `lock-busy` (rc=11) を繰り返し、
  76 分間 main が 1 度も進まなかった。dev-wave-jobs 配下の land 結果 JSON では、20:00〜22:10 に
  `window_elapsed_s=180.00` (initial で 180 秒待ち切り) と `300〜825` (監査後・fold gate 後の再取得で待ち切り)
  が交互に並ぶ。manager session が手で 1 本ずつ GO を渡すと 2 波 30 本が失敗 0・5〜6 分/本で流れた。
- 根本原因: 非 noop fold の land は共通 flock を 3 回 (initial / post-provenance / post-fold-gate) 取り直し、
  再取得は先着順でも公平でもない (D432 は公平性を保証しない)。到着率 (各 session の再投入) が処理率を超えると
  initial の待ち行列が伸び続け、監査から帰ってきた holder は毎回その後ろに並んで 180 秒の累積予算を使い切る。
  D1996 が直したのは「lock 外の作業時間を予算から差し引く混同」で、再取得競走そのものは残っていた。
  別経路として、cleanup が他 wave を撤去する瞬間に `_worktree_snapshot` が無関係 child の `.git` を
  開いてから読む race で `RC_CONTROL_PLANE` を出す事象も同じ窓で観測されたが、件数は分離していない。
- 恒久対応: {{D:land-turn-ticket}} — 受入 lease と別の land 順番票 (FD lock 生存・非横取り grant・原子的引渡し)、
  lock-busy で監査・fold gate の証拠を捨てない二層予算、無関係 child の非接触。`tools/dev_wave_land.py` と
  `orchestrator/tests/test_dev_wave_land.py` の決定的 scheduler test が fails-closed に検査する。
- 再発検知: land 結果 JSON の `status=lock-busy` が同一 wave で 3 回以上続き、reason に
  `waiting for land turn` が無い (= 順番票を知らない旧 driver か、旧 driver との混在) なら本件の型。
  順番票あり同士で起きたら D の前提 (先頭が有限時間で進む) の破れを疑い、先頭 ticket の phase と
  registry の grant を読む。
